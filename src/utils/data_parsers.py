"""
Data parsing utilities for handling complex data formats in CSV files.
"""
import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def parse_monthly_enrollment(months_string: str) -> List[int]:
    """
    Parse comma-separated monthly enrollment string.
    
    The enrollment_rate_report table stores monthly data as:
    "5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8" (12 values for Jan-Dec)
    
    Args:
        months_string: Comma-separated string of monthly enrollment counts
        
    Returns:
        List of integers representing enrollment for each month
        
    Example:
        >>> parse_monthly_enrollment("5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8")
        [5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8]
    """
    try:
        if not months_string or months_string.strip() == '':
            return []
        
        # Remove quotes if present
        months_string = months_string.strip('"').strip("'")
        
        # Split by comma and convert to integers
        values = [int(x.strip()) for x in months_string.split(',') if x.strip()]
        
        return values
    
    except Exception as e:
        logger.error(f"Error parsing monthly enrollment '{months_string}': {e}")
        return []


def calculate_weekly_enrollment(months_string: str, recent_months: int = 1) -> float:
    """
    Calculate average weekly enrollment from recent months.
    
    Assumes each month = 4 weeks for simplification.
    
    Args:
        months_string: Comma-separated string of monthly enrollment
        recent_months: Number of recent months to consider (default: 1)
        
    Returns:
        Average weekly enrollment rate
        
    Example:
        >>> calculate_weekly_enrollment("5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8", recent_months=1)
        2.0  # Last month (8) / 4 weeks
    """
    try:
        monthly_data = parse_monthly_enrollment(months_string)
        
        if not monthly_data:
            return 0.0
        
        # Get recent months (from the end of the list)
        recent_data = monthly_data[-recent_months:] if len(monthly_data) >= recent_months else monthly_data
        
        # Calculate average monthly enrollment
        avg_monthly = sum(recent_data) / len(recent_data) if recent_data else 0
        
        # Convert to weekly (assuming 4 weeks per month)
        weekly_avg = avg_monthly / 4.0
        
        return weekly_avg
    
    except Exception as e:
        logger.error(f"Error calculating weekly enrollment: {e}")
        return 0.0


def calculate_8week_demand(months_string: str) -> float:
    """
    Calculate projected 8-week demand based on recent enrollment.
    
    Uses the last month's data to project 8 weeks forward.
    
    Args:
        months_string: Comma-separated string of monthly enrollment
        
    Returns:
        Projected demand for next 8 weeks
        
    Example:
        >>> calculate_8week_demand("5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8")
        16.0  # (8 patients/month / 4 weeks) * 8 weeks = 16
    """
    weekly_avg = calculate_weekly_enrollment(months_string, recent_months=1)
    return weekly_avg * 8


def parse_shipping_timeline(timeline_text: str) -> int:
    """
    Parse shipping timeline text to extract number of days.
    
    The ip_shipping_timelines_report table stores timelines as:
    "6 days door-to-door", "13 days door-to-door", etc.
    
    Args:
        timeline_text: Timeline description text
        
    Returns:
        Number of days as integer, 0 if parsing fails
        
    Example:
        >>> parse_shipping_timeline("6 days door-to-door")
        6
        >>> parse_shipping_timeline("13 days door-to-door")
        13
    """
    try:
        if not timeline_text:
            return 0
        
        # Extract number before "days" or "day"
        match = re.search(r'(\d+)\s*days?', timeline_text, re.IGNORECASE)
        
        if match:
            return int(match.group(1))
        
        logger.warning(f"Could not parse shipping timeline: '{timeline_text}'")
        return 0
    
    except Exception as e:
        logger.error(f"Error parsing shipping timeline '{timeline_text}': {e}")
        return 0


def extract_location_from_ip_helper(ip_helper_text: str) -> Optional[str]:
    """
    Extract location/country from ip_helper text.
    
    The ip_helper field contains text like:
    "Coreyshire Logistics Center (Saint Kitts and Nevis)"
    
    Args:
        ip_helper_text: IP helper description
        
    Returns:
        Extracted location/country or None
        
    Example:
        >>> extract_location_from_ip_helper("Coreyshire Logistics Center (Saint Kitts and Nevis)")
        "Saint Kitts and Nevis"
    """
    try:
        if not ip_helper_text:
            return None
        
        # Extract text within parentheses
        match = re.search(r'\(([^)]+)\)', ip_helper_text)
        
        if match:
            return match.group(1).strip()
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting location from '{ip_helper_text}': {e}")
        return None


def calculate_stockout_date(
    current_stock: int,
    weekly_enrollment: float,
    current_date_str: str = None
) -> Optional[str]:
    """
    Calculate estimated stockout date based on current stock and enrollment rate.
    
    Args:
        current_stock: Current inventory quantity
        weekly_enrollment: Average weekly enrollment/consumption rate
        current_date_str: Current date as string (YYYY-MM-DD), uses today if None
        
    Returns:
        Estimated stockout date as string (YYYY-MM-DD) or None if no stockout expected
        
    Example:
        >>> calculate_stockout_date(100, 10.0, "2025-01-01")
        "2025-03-12"  # 100 / 10 = 10 weeks = 70 days
    """
    try:
        from datetime import datetime, timedelta
        
        if weekly_enrollment <= 0:
            return None  # No consumption, no stockout
        
        if current_stock <= 0:
            return current_date_str or datetime.now().strftime('%Y-%m-%d')  # Already out of stock
        
        # Calculate weeks until stockout
        weeks_until_stockout = current_stock / weekly_enrollment
        
        # Convert to days
        days_until_stockout = int(weeks_until_stockout * 7)
        
        # Calculate stockout date
        if current_date_str:
            current_date = datetime.strptime(current_date_str, '%Y-%m-%d')
        else:
            current_date = datetime.now()
        
        stockout_date = current_date + timedelta(days=days_until_stockout)
        
        return stockout_date.strftime('%Y-%m-%d')
    
    except Exception as e:
        logger.error(f"Error calculating stockout date: {e}")
        return None


def classify_expiry_severity(days_remaining: int) -> str:
    """
    Classify expiry severity based on days remaining.
    
    Args:
        days_remaining: Number of days until expiry
        
    Returns:
        Severity level: CRITICAL, HIGH, or MEDIUM
        
    Example:
        >>> classify_expiry_severity(25)
        "CRITICAL"
        >>> classify_expiry_severity(45)
        "HIGH"
        >>> classify_expiry_severity(75)
        "MEDIUM"
    """
    if days_remaining < 30:
        return "CRITICAL"
    elif days_remaining < 60:
        return "HIGH"
    else:
        return "MEDIUM"


# Utility function for testing
if __name__ == "__main__":
    # Test monthly enrollment parsing
    test_months = "5, 4, 5, 4, 6, 0, 8, 10, 4, 8, 4, 8"
    print(f"Monthly data: {parse_monthly_enrollment(test_months)}")
    print(f"Weekly avg (last month): {calculate_weekly_enrollment(test_months, 1)}")
    print(f"8-week demand: {calculate_8week_demand(test_months)}")
    
    # Test shipping timeline parsing
    test_timeline = "6 days door-to-door"
    print(f"Shipping days: {parse_shipping_timeline(test_timeline)}")
    
    # Test location extraction
    test_ip_helper = "Coreyshire Logistics Center (Saint Kitts and Nevis)"
    print(f"Location: {extract_location_from_ip_helper(test_ip_helper)}")
    
    # Test stockout calculation
    print(f"Stockout date: {calculate_stockout_date(100, 10.0, '2025-01-01')}")
    
    # Test severity classification
    print(f"Severity (25 days): {classify_expiry_severity(25)}")
    print(f"Severity (45 days): {classify_expiry_severity(45)}")
    print(f"Severity (75 days): {classify_expiry_severity(75)}")
