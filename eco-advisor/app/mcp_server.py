import sys
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("EcoAdvisor MCP Server")

@mcp.tool()
def calculate_carbon_footprint(activity_type: str, quantity: float) -> str:
    """Calculate the carbon footprint of an activity.

    Args:
        activity_type: The type of activity (one of: 'electricity_kwh', 'driving_miles', 'flight_hours').
        quantity: The quantity of the activity (e.g. kWh, miles, hours).
    
    Returns:
        A string summarizing the carbon footprint in kg CO2.
    """
    factors = {
        "electricity_kwh": 0.385,    # kg CO2/kWh
        "driving_miles": 0.404,      # kg CO2/mile
        "flight_hours": 90.0         # kg CO2/hour (per passenger)
    }
    
    act_lower = activity_type.lower().strip()
    if act_lower not in factors:
        return f"Unknown activity type '{activity_type}'. Supported: {list(factors.keys())}"
        
    factor = factors[act_lower]
    emissions = quantity * factor
    return f"Activity: {activity_type}, Quantity: {quantity}. Estimated carbon impact: {emissions:.2f} kg CO2."

@mcp.tool()
def get_recycling_rules(material: str, zip_code: str = "") -> str:
    """Get waste sorting and recycling guidelines for a specific material.

    Args:
        material: The material to dispose of (e.g. 'plastic bottle', 'cardboard', 'battery', 'aluminum can').
        zip_code: Optional zip code for localized rules.
    
    Returns:
        Recycling instructions for the material.
    """
    material_lower = material.lower().strip()
    
    rules = {
        "plastic bottle": "Recyclable. Empty, rinse, replace cap, and place in the standard blue recycling bin.",
        "cardboard": "Recyclable. Flatten the box, remove tape/shipping labels if possible, and keep dry in the recycling bin.",
        "aluminum can": "Highly recyclable. Rinse lightly and place in the blue recycling bin. Do not crush if local rules prefer intact cans.",
        "battery": "Hazardous Waste. Do NOT throw in trash or standard recycling. Take to a local household hazardous waste facility or drop-off location (e.g. home improvement store)."
    }
    
    for key, rule in rules.items():
        if key in material_lower:
            loc_str = f" in ZIP {zip_code}" if zip_code else ""
            return f"Recycling guidelines for '{material}'{loc_str}: {rule}"
            
    return f"Recycling guidelines for '{material}': Place in general waste or check local special disposal facilities (hazardous/e-waste) if it contains chemicals or electronics."

@mcp.tool()
def search_eco_products(product_category: str) -> str:
    """Find eco-friendly and sustainable alternatives for standard product categories.

    Args:
        product_category: The category of product (e.g. 'detergent', 'toothbrush', 'water bottle').
    
    Returns:
        Recommendations for eco-friendly product alternatives.
    """
    cat_lower = product_category.lower().strip()
    
    alternatives = {
        "detergent": "Try eco-sheets, soap nuts, or zero-waste liquid detergent refills that use compostable cardboard packaging.",
        "toothbrush": "Switch to a bamboo toothbrush with biodegradable bristles, or toothbrushes with replaceable heads.",
        "water bottle": "Use a reusable food-grade stainless steel or glass water bottle instead of single-use plastic bottles.",
        "bag": "Use organic cotton tote bags or reusable mesh produce bags instead of paper or plastic shopping bags."
    }
    
    for key, alt in alternatives.items():
        if key in cat_lower:
            return f"Eco-friendly alternatives for '{product_category}': {alt}"
            
    return f"Eco-friendly alternatives for '{product_category}': Look for certified plastic-free, biodegradable, or reusable versions of this product."

@mcp.tool()
def get_composting_guideline(item_name: str) -> str:
    """Check if an item is compostable and get instructions on how to compost it.

    Args:
        item_name: The name of the item to compost (e.g. 'apple core', 'paper towel', 'plastic bag').
    
    Returns:
        Composting instructions for the item.
    """
    item_lower = item_name.lower().strip()
    
    if any(k in item_lower for k in ["apple", "banana", "core", "peel", "food", "vegetable", "fruit", "coffee"]):
        return f"'{item_name}' is Green Compostable. Place in green bin or home compost pile. Decomposes quickly."
    elif any(k in item_lower for k in ["paper towel", "napkin", "cardboard tube", "leaves"]):
        return f"'{item_name}' is Brown Compostable. Tear into small pieces to help decomposition, and add to the compost pile."
    elif any(k in item_lower for k in ["plastic bag", "foil", "metal", "meat", "dairy"]):
        return f"'{item_name}' is NOT compostable in standard home bins. Foil and plastic bags must be recycled/trashed. Meat/dairy attract pests; compost only in specialized industrial facilities."
        
    return f"Composting status for '{item_name}': Organic matter is generally compostable. If it's plant-based food or clean paper, compost it. If it contains plastics, meats, or chemicals, avoid composting."

if __name__ == "__main__":
    mcp.run("stdio")
