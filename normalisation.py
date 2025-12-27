# Normalisation layer public API
# from __future__ import annotations
# 
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import masters
from .lookups import (
	lookup_caste_by_any_field,
	lookup_height_exact,
	lookup_address_by_pincode,
	lookup_qualification,
	lookup_occupation,
	lookup_marital_status,
	lookup_manglik,
	parse_education_specialization,
)
from .helpers import (
	clean_str,
	parse_name,
	normalize_age,
	normalize_date,
	normalize_via_master,
	normalize_height,
	normalize_country_state,
	normalize_birth_time,
	normalize_height_format,
	summarize_about_yourself,
	normalize_marital_status,
	normalize_manglik,
)
from .geocoding import lookup_zipcode_by_address, extract_address_components, find_closest_zipcode
from .gender_detection import auto_detect_gender, ensure_gender_present
from .unstructured_extractor import enrich_profile_from_unstructured_text

DEFAULT_CONFIG = {
	# Default master_dir set to project-level Data/training folder where
	# master Excel files are stored (adjust if your masters live elsewhere).
	"master_dir": Path(__file__).resolve().parent.parent / "Data" / "training",
	"scorer": "auto",
	"threshold": 80.0,  # percent threshold for accepting fuzzy matches
}


def _load_schema(master_dir: Optional[Path]) -> List[str]:
	try:
		return masters.load_biodata_output_schema(master_dir)
	except FileNotFoundError:
		# Fallback schema — callers should place `Biodata_Output.xlsx` in masters dir.
		return [
			"full_name",
			"first_name",
			"last_name",
			"gender",
			"date_of_birth",
			"age",
			"birth_time",
			"birth_place",
			"height",
			"marital_status",
			"religion",
			"caste",
			"jaati",
			"gotra",
			"sakha",
			"manglik",
			"education",
			"specialization",
			"occupation",
			"annual_income",
			"address",
			"village",
			"tahsil",
			"district",
			"native_state",
			"state",
			"city",
			"country",
			"zip_code",
			"email_id",
			"mobile_no",
			"phone_no",
			"about_yourself_summary",
		]

def normalize_profile(raw_profile: Dict[str, Any]) -> Dict[str, Any]:
	"""Normalize a raw extracted profile into the canonical biodata schema.

	This function is the single public entrypoint for the Normalisation layer.

	Rules (lenient mode):
	- Uses fuzzy matching against master sheets (see Normalisation/masters.py).
	- If match confidence < `threshold`, the field is set to None.
	- Does not invent or modify master values.

	Args:
		raw_profile: raw dict produced by Extraction/LLM Extraction layer.

	Returns:
		A dict whose keys are the columns defined in `Biodata_Output.xlsx` (if present),
		or a reasonable fallback schema. Values are canonical master values or None.
	"""
	cfg = DEFAULT_CONFIG
	master_dir = Path(cfg["master_dir"]) if cfg["master_dir"] else None
	scorer = cfg["scorer"]
	threshold = float(cfg["threshold"])

	output_columns = _load_schema(master_dir)
	out: Dict[str, Any] = {k: None for k in output_columns}

	# Helpers to read common raw names
	def _get(*keys: str):
		for k in keys:
			if k in raw_profile and raw_profile[k] is not None:
				return raw_profile[k]
		return None
	
	# Helper to get values from PascalCase keys (for customer_data compatibility)
	def _get_pascal(*keys: str):
		"""Try to find values from both snake_case and PascalCase keys"""
		for k in keys:
			if k in raw_profile and raw_profile[k] is not None:
				return raw_profile[k]
			# Try PascalCase variant
			pascal = ''.join(word.capitalize() for word in k.split('_'))
			if pascal in raw_profile and raw_profile[pascal] is not None:
				return raw_profile[pascal]
		return None

	# Full name and split
	full_name_raw = _get_pascal("full_name", "name", "FullName", "fullname")
	
	# If no full name, try to build from first/last
	if not full_name_raw:
		first_name_raw = _get_pascal("first_name", "FirstName")
		last_name_raw = _get_pascal("last_name", "LastName")
		if first_name_raw or last_name_raw:
			parts = []
			if first_name_raw:
				parts.append(str(first_name_raw).strip())
			if last_name_raw:
				parts.append(str(last_name_raw).strip())
			full_name_raw = " ".join(parts) if parts else None
	
	full_name = clean_str(full_name_raw)
	first, last = parse_name(full_name)
	if "full_name" in out:
		out["full_name"] = full_name
	if "first_name" in out:
		out["first_name"] = first
	if "last_name" in out:
		out["last_name"] = last

	# Age and date_of_birth
	dob_raw = _get_pascal("date_of_birth", "dob", "DOB", "DateOfBirth")
	dob_iso = normalize_date(dob_raw)
	age_raw = _get_pascal("age", "Age")
	age_int = normalize_age(age_raw)
	# if age missing but dob present, compute age
	if age_int is None and dob_iso:
		try:
			from datetime import date

			y = int(dob_iso.split("-")[0])
			age_int = date.today().year - y
			if age_int <= 0 or age_int > 120:
				age_int = None
		except Exception:
			age_int = None
	if "age" in out:
		out["age"] = age_int
	if "date_of_birth" in out:
		out["date_of_birth"] = dob_iso

	# Birth time and birth place
	if "birth_time" in out:
		birth_time_raw = clean_str(_get_pascal("birth_time", "birthtime", "BirthTime"))
		if birth_time_raw:
			# Convert to 12-hour format with A.M./P.M.
			birth_time_normalized = normalize_birth_time(birth_time_raw)
			out["birth_time"] = birth_time_normalized if birth_time_normalized else birth_time_raw
		else:
			out["birth_time"] = None
	if "birth_place" in out:
		out["birth_place"] = clean_str(_get_pascal("birth_place", "birthplace", "BirthPlace"))

	# Gender
	if "gender" in out:
		gender_val = clean_str(_get_pascal("gender", "sex", "Gender"))
		# Standardize gender values
		if gender_val:
			gender_lower = gender_val.lower().strip()
			if gender_lower in ['m', 'male', 'boy']:
				out["gender"] = "Male"
			elif gender_lower in ['f', 'female', 'girl', 'woman']:
				out["gender"] = "Female"
			else:
				out["gender"] = gender_val  # Keep as-is if not recognized
		else:
			# Try to auto-detect gender if not provided
			inferred = auto_detect_gender(raw_profile)
			out["gender"] = inferred

	# Marital status - STRICT lookup from master only
	if "marital_status" in out:
		marital_raw = clean_str(_get_pascal("marital_status", "maritalstatus", "MaritialStatus"))
		if marital_raw:
			# STRICT: try master lookup first
			marital_val = lookup_marital_status(marital_raw, master_dir=master_dir)
			# Fallback: try local normalization (maps common variants to allowed list)
			if not marital_val:
				marital_val = normalize_marital_status(marital_raw, scorer=scorer, threshold=threshold)
			out["marital_status"] = marital_val
		else:
			out["marital_status"] = None

	# Enforce marital status to the allowed canonical set from business rules
	if "marital_status" in out:
		allowed = [
			"Awaiting Divorce",
			"Committed",
			"Divorced",
			"Married",
			"Un-Married",
			"Widow",
			"Widower",
		]
		ms_raw_val = out.get("marital_status") or clean_str(_get_pascal("marital_status", "maritalstatus", "MaritialStatus"))
		matched = None
		if ms_raw_val:
			mv = str(ms_raw_val).strip()
			# exact case-insensitive match
			for a in allowed:
				if a.lower() == mv.lower():
					matched = a
					break
			# substring/contains heuristics
			if not matched:
				for a in allowed:
					if a.lower() in mv.lower() or mv.lower() in a.lower():
						matched = a
						break
			# fuzzy match as last resort using fuzzywuzzy if available
			if not matched:
				try:
					from fuzzywuzzy import process as fuzzy_process
					cand = fuzzy_process.extractOne(mv, allowed)
					if cand and cand[1] >= threshold:
						matched = cand[0]
				except Exception:
					pass
		# If nothing matches, set to None (do not hallucinate)
		out["marital_status"] = matched if matched else None

	# Manglik - STRICT lookup from master only
	if "manglik" in out:
		manglik_val = clean_str(_get_pascal("manglik", "Manglik"))
		if manglik_val:
			# STRICT: try master lookup first
			manglik_result = lookup_manglik(manglik_val, master_dir=master_dir)
			# Fallback: try local normalization to allowed values
			if not manglik_result:
				manglik_result = normalize_manglik(manglik_val, scorer=scorer, threshold=threshold)
			out["manglik"] = manglik_result
		else:
			out["manglik"] = None

	# Ensure `manglik` is always one of: "Yes", "No", "Don't Know"
	if "manglik" in out:
		m_val = out.get("manglik") or clean_str(_get_pascal("manglik", "Manglik"))
		if m_val:
			mv = str(m_val).lower()
			if mv in ["yes", "y", "true", "t", "manglik"] or "yes" in mv:
				out["manglik"] = "Yes"
			elif mv in ["no", "n", "false", "f", "non-manglik", "non manglik"] or "no" in mv or "non" in mv:
				out["manglik"] = "No"
			else:
				out["manglik"] = "Don't Know"
		else:
			out["manglik"] = "Don't Know"

	# Religion
	if "religion" in out:
		out["religion"] = clean_str(_get_pascal("religion", "Religion"))

	# Caste and related fields - Enhanced lookup
	# Try to lookup by any caste-related field (Jaati, Caste, Gotra, Sakha)
	# Prioritize more specific fields (gotra, sakha) over general ones (caste, jaati)
	# If any value matches, return the complete row from master
	
	# Try fields in order of specificity (most specific first)
	caste_lookup_value = None
	for field in ["gotra", "sakha", "jaati", "caste", "community", "Gotra", "Sakha", "Jaati", "Caste"]:
		caste_lookup_value = _get_pascal(field)
		if caste_lookup_value:
			break
	
	if caste_lookup_value:
		caste_data = lookup_caste_by_any_field(caste_lookup_value, master_dir=master_dir)
		if caste_data:
			# Found in master - populate all caste fields from master row
			if "jaati" in out:
				out["jaati"] = caste_data.get("jaati") or out["jaati"]
			if "caste" in out:
				out["caste"] = caste_data.get("caste") or out["caste"]
			if "gotra" in out:
				out["gotra"] = caste_data.get("gotra") or out["gotra"]
			if "sakha" in out:
				out["sakha"] = caste_data.get("sakha") or out["sakha"]
		else:
			# Not found in master - fallback to old logic with individual fields
			if "jaati" in out:
				jaati_raw = _get_pascal("jaati", "caste", "community")
				jaati_master = []
				try:
					jaati_master = masters.get_master_values("caste", column="Jaati", master_dir=master_dir)
				except Exception:
					pass
				jaati_val = normalize_via_master(jaati_raw, jaati_master, scorer=scorer, threshold=threshold)
				out["jaati"] = jaati_val
			
			if "caste" in out:
				caste_raw = _get_pascal("caste", "Caste")
				caste_master = []
				try:
					caste_master = masters.get_master_values("caste", column="Caste", master_dir=master_dir)
				except Exception:
					pass
				caste_val = normalize_via_master(caste_raw, caste_master, scorer=scorer, threshold=threshold)
				out["caste"] = caste_val
			
			if "gotra" in out:
				gotra_raw = _get_pascal("gotra", "Gotra")
				gotra_master = []
				try:
					gotra_master = masters.get_master_values("caste", column="Gotra", master_dir=master_dir)
				except Exception:
					pass
				gotra_val = normalize_via_master(gotra_raw, gotra_master, scorer=scorer, threshold=threshold)
				out["gotra"] = gotra_val
			
			if "sakha" in out:
				sakha_raw = _get_pascal("sakha", "Sakha")
				sakha_master = []
				try:
					sakha_master = masters.get_master_values("caste", column="Sakha", master_dir=master_dir)
				except Exception:
					pass
				sakha_val = normalize_via_master(sakha_raw, sakha_master, scorer=scorer, threshold=threshold)
				out["sakha"] = sakha_val


	# Education and specialization - STRICT lookup with parsing from master
	# If education contains both degree and specialization (e.g., "Msc(IT)"),
	# split and look up both components in masters
	if "education" in out:
		qual_raw = _get_pascal("education", "qualification", "degree", "Education")
		if qual_raw:
			# Try to parse education/specialization from combined string
			education_val, specialization_val = parse_education_specialization(qual_raw, master_dir=master_dir)
			out["education"] = education_val  # Will be None if not found in master
			
			# If we got specialization from parsing, use it
			if "specialization" in out and specialization_val:
				out["specialization"] = specialization_val
		else:
			out["education"] = None
	
	# If specialization not already set from education parsing, try direct lookup
	if "specialization" in out and not out.get("specialization"):
		spec_raw = clean_str(_get_pascal("specialization", "field_of_study", "Specialization"))
		if spec_raw:
			out["specialization"] = spec_raw
		else:
			out["specialization"] = None

	# Occupation and income - Enhanced lookup
	if "occupation" in out:
		occ_raw = _get_pascal("occupation", "job", "profession", "Occupation")
		if occ_raw:
			# Try lookup first (returns master value if found)
			occ_val = lookup_occupation(occ_raw, master_dir=master_dir)
			out["occupation"] = occ_val
		else:
			out["occupation"] = None
	
	if "annual_income" in out:
		out["annual_income"] = clean_str(_get_pascal("annual_income", "income", "AnnualIncome"))

	# Address and location fields - with zip code lookup and reverse geocoding
	address_raw = clean_str(_get("address"))
	if "address" in out:
		out["address"] = address_raw
	
	# Collect current address components
	current_city = clean_str(_get_pascal("city", "City"))
	current_state = clean_str(_get_pascal("state", "region", "State"))

	# Defensive: ignore values that look like educational institutions or addresses
	def _is_institution_like(val: Optional[str]) -> bool:
		if not val:
			return False
		v = str(val).lower()
		# common institution/address indicators
		indicators = ["university", "college", "institute", "department", "faculty", "school", "hospital"]
		if any(ind in v for ind in indicators):
			return True
		# commas/semicolons usually indicate address or institution with location
		if "," in v or ";" in v:
			return True
		return False

	# If extracted state looks like an institution, discard it so later lookups can fill it
	if _is_institution_like(current_state):
		current_state = None
	current_district = clean_str(_get_pascal("district", "District"))
	
	# Try to lookup address by pin code first
	zip_code_raw = _get_pascal("zip_code", "zipcode", "postal_code", "pincode", "pin", "ZipCode")
	if zip_code_raw:
		zip_code_raw = str(zip_code_raw).strip()
		address_data = lookup_address_by_pincode(zip_code_raw, master_dir=master_dir)
		if address_data:
			# Found address data for this pin code - populate missing fields
			if "country" in out and not out["country"]:
				out["country"] = address_data.get("country")
			if "state" in out and not out["state"]:
				out["state"] = address_data.get("state")
			if "city" in out and not out["city"]:
				out["city"] = address_data.get("city")
			if "district" in out and not out["district"]:
				out["district"] = address_data.get("district")
			if "zip_code" in out and not out["zip_code"]:
				out["zip_code"] = zip_code_raw
	
	# If we have address but no zip code, try reverse geocoding
	if address_raw and not out.get("zip_code"):
		zipcode_result = lookup_zipcode_by_address(
			address_raw, 
			city=current_city, 
			state=current_state, 
			master_dir=master_dir
		)
		if zipcode_result:
			if "zip_code" in out and not out["zip_code"]:
				out["zip_code"] = zipcode_result.get("zip_code") or zipcode_result.get("postal_code")
			if "city" in out and not out["city"]:
				out["city"] = zipcode_result.get("city")
			if "state" in out and not out["state"]:
				out["state"] = zipcode_result.get("state")
			if "country" in out and not out["country"]:
				out["country"] = zipcode_result.get("country")
			if "district" in out and not out["district"]:
				out["district"] = zipcode_result.get("district")
	
	if "village" in out:
		out["village"] = clean_str(_get_pascal("village", "Village"))
	if "tahsil" in out:
		out["tahsil"] = clean_str(_get_pascal("tahsil", "Tahsil"))
	if "district" in out:
		out["district"] = out.get("district") or clean_str(_get_pascal("district", "District"))
	if "native_state" in out:
		native_state_value = clean_str(_get_pascal("native_state", "nativestate", "NativeState"))
		out["native_state"] = native_state_value if native_state_value else "Rajasthan"  # Default to Rajasthan
	if "city" in out:
		out["city"] = out.get("city") or current_city
	if "zip_code" in out:
		out["zip_code"] = out.get("zip_code") or clean_str(_get_pascal("zip_code", "zipcode", "postal_code", "pincode", "ZipCode"))

	# Zip code fallbacks: try to extract from address text or search CountryStateMst
	if "zip_code" in out and not out.get("zip_code"):
		# 1) Try simple extraction from full address
		try:
			components = extract_address_components(address_raw or "", master_dir=master_dir)
		except Exception:
			components = None
		if components and components.get("zip_code"):
			out["zip_code"] = components.get("zip_code")
		# 2) If still not found, try to find closest zipcode from partial address fields
		if not out.get("zip_code"):
			# Build a partial address from available fields
			parts = []
			for fld in (address_raw, out.get("city"), out.get("district"), out.get("state"), out.get("birth_place")):
				if fld:
					parts.append(str(fld))
			partial = ", ".join(parts)
			if partial:
				try:
					matches = find_closest_zipcode(partial, master_dir=master_dir, threshold=65)
				except Exception:
					matches = []
				if matches:
					first = matches[0]
					# common column keys may be 'zip_code' or 'pincode' etc.
					zipc = first.get("zip_code") or first.get("pincode") or first.get("postal_code")
					if zipc:
						out["zip_code"] = zipc

	# Country and State
	if "country" in out or "state" in out:
		country_raw = _get_pascal("country", "nationality", "Country")
		state_raw = _get_pascal("state", "region", "State")
		country_state_df = None
		try:
			country_state_df = masters.load_master("country_state", master_dir=master_dir)
		except Exception:
			pass
		country_val, state_val = normalize_country_state(country_raw, state_raw, country_state_df, scorer=scorer, threshold=threshold)
		if "country" in out:
			out["country"] = country_val
		if "state" in out:
			out["state"] = state_val

	# Height - lookup exact match from master, fallback to standardized format
	if "height" in out:
		height_raw = _get_pascal("height", "Height", "height_cm")
		if height_raw:
			# Try lookup first (returns master value if found)
			height_val = lookup_height_exact(height_raw, master_dir=master_dir)
			# Fallback: if not in master, convert to standard format "xft yin (in cms)"
			if not height_val:
				height_val = normalize_height_format(height_raw)
				# If still no value, try the old normalization
				if not height_val:
					height_val = normalize_height(height_raw, [], scorer=scorer, threshold=threshold)
			out["height"] = height_val
		else:
			out["height"] = None

	# Contact fields
	if "email_id" in out:
		out["email_id"] = clean_str(_get_pascal("email_id", "email", "EmailId"))
	if "mobile_no" in out:
		out["mobile_no"] = clean_str(_get_pascal("mobile_no", "mobile", "phone", "contact", "MobileNo"))
	if "phone_no" in out:
		out["phone_no"] = clean_str(_get_pascal("phone_no", "phone", "PhoneNo"))

	# Enrich from unstructured text if available
	unstructured_text = _get("notes", "description", "text", "raw_text", "comments", "about_yourself", "ABOUT YOURSELF")
	if unstructured_text:
		try:
			out = enrich_profile_from_unstructured_text(out, str(unstructured_text))
		except Exception:
			# If enrichment fails, continue with current out
			pass
		
		# Add ABOUT YOURSELF summary if field exists in schema
		if "about_yourself_summary" in out:
			out["about_yourself_summary"] = summarize_about_yourself(str(unstructured_text))

	return out

__all__ = ["normalize_profile"]
