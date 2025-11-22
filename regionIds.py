import json
import sys
from typing import Any, Dict, Iterable, List, Set
import requests

'''
This script is used to get all region ids for a query location.
These region ids can then be used to retrieve all listings for a given location.
'''


ZILLOW_GRAPH_ENDPOINT = "https://www.zillow.com/zg-graph"


GRAPHQL_QUERY = """
query GetAutocompleteResults($query: String!, $queryOptions: SearchAssistanceQueryOptions, $resultType: [SearchAssistanceResultType], $shouldRequestSpellCorrectedMetadata: Boolean = false) {
  searchAssistanceResult: zgsAutocompleteRequest(
    query: $query
    queryOptions: $queryOptions
    resultType: $resultType
  ) {
    requestId
    results {
      ...SearchAssistanceResultFields
      ...RegionResultFields
      ...SemanticResultFields
      ...RentalCommunityResultFields
      ...SchoolResultFields
      ...BuilderCommunityResultFields
    }
  }
}

fragment SearchAssistanceResultFields on SearchAssistanceResult {
  __typename
  id
  spellCorrectedMetadata @include(if: $shouldRequestSpellCorrectedMetadata) {
    ...SpellCorrectedFields
  }
}

fragment SpellCorrectedFields on SpellCorrectedMetadata {
  isSpellCorrected
  spellCorrectedQuery
  userQuery
}

fragment RegionResultFields on SearchAssistanceRegionResult {
  regionId
  subType
  state
  county
  city
}

fragment SchoolResultFields on SearchAssistanceSchoolResult {
  id
  schoolDistrictId
  schoolId
}

fragment SemanticResultFields on SearchAssistanceSemanticResult {
  nearMe
  regionIds
  regionTypes
  regionDisplayIds
  queryResolutionStatus
  schoolDistrictIds
  schoolIds
  viewLatitudeDelta
  filters {
    basementStatusType
    baths { min max }
    beds { min max }
    excludeTypes
    hoaFeesPerMonth { min max }
    homeType
    keywords
    listingStatusType
    livingAreaSqft { min max }
    lotSizeSqft { min max }
    parkingSpots { min max }
    price { min max }
    searchRentalFilters {
      monthlyPayment { min max }
      petsAllowed
      rentalAvailabilityDate { min max }
    }
    searchSaleFilters { daysOnZillow { min max } }
    showOnlyType
    view
    yearBuilt { min max }
  }
}

fragment RentalCommunityResultFields on SearchAssistanceRentalCommunityResult {
  location { latitude longitude }
}

fragment BuilderCommunityResultFields on SearchAssistanceBuilderCommunityResult {
  plid
}
"""


def build_headers() -> Dict[str, str]:
    return {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": "https://www.zillow.com",
        "referer": "https://www.zillow.com/",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "x-caller-id": "static-search-page-graphql",
    }


def build_variables(query_text: str, max_results: int = 100) -> Dict[str, Any]:
    return {
        "query": query_text,
        "queryOptions": {
            "maxResults": max_results,
            "userSearchContext": "FOR_SALE",
            "spellCheck": False,
        },
        "resultType": [
            "REGIONS",
            "FORSALE",
            "RENTALS",
            "SOLD",
            "COMMUNITIES",
            "SCHOOLS",
            "SCHOOL_DISTRICTS",
            "BUILDER_COMMUNITIES",
        ],
        "shouldRequestSpellCorrectedMetadata": False,
    }


def fetch_autocomplete_results(query_text: str, timeout_seconds: int = 20) -> Dict[str, Any]:
    payload = {
        "operationName": "GetAutocompleteResults",
        "variables": build_variables(query_text),
        "query": GRAPHQL_QUERY,
    }
    response = requests.post(
        ZILLOW_GRAPH_ENDPOINT,
        headers=build_headers(),
        json=payload,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def extract_region_ids(graph_response: Dict[str, Any]) -> List[int]:
    results: Iterable[Dict[str, Any]] = (
        graph_response
        .get("data", {})
        .get("searchAssistanceResult", {})
        .get("results", [])
    )
    region_ids: Set[int] = set()
    for item in results:
        typename = item.get("__typename")
        if typename == "SearchAssistanceRegionResult":
            region_id = item.get("regionId")
            if isinstance(region_id, int):
                region_ids.add(region_id)
        elif typename == "SearchAssistanceSemanticResult":
            # Semantic results can include a list of regionIds
            for rid in item.get("regionIds", []) or []:
                if isinstance(rid, int):
                    region_ids.add(rid)
    return sorted(region_ids)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python api.py \"<query>\"")
        sys.exit(1)

    query_text = sys.argv[1]
    try:
        data = fetch_autocomplete_results(query_text)
        print(data["data"]["searchAssistanceResult"]["results"])
        # region_ids = extract_region_ids(data)
    except requests.HTTPError as http_err:
        print(json.dumps({"error": f"HTTP {http_err.response.status_code}", "details": str(http_err)}))
        sys.exit(2)
    except Exception as exc:  # noqa: BLE001 - show all errors to aid debugging
        print(json.dumps({"error": "RequestFailed", "details": str(exc)}))
        sys.exit(3)


if __name__ == "__main__":
    main()


