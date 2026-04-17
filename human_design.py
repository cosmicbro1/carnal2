"""
Human Design Chart Generator & Compatibility Matcher
Generates HD charts from birth data and matches compatibility
"""
from datetime import datetime
from typing import Dict, Optional, Tuple
import json

# Human Design System data
TYPES = {
    "Manifestor": {"strategy": "Inform", "aura": "Closed and Repelling", "direction": "Initiate"},
    "Generator": {"strategy": "Respond", "aura": "Open and Enveloping", "direction": "Work"},
    "Generator Crossing": {"strategy": "Respond", "aura": "Open and Enveloping", "direction": "Work & Attract"},
    "Reflector": {"strategy": "Wait a lunar cycle", "aura": "Sampling", "direction": "Reflect"},
}

# 64 I Ching Hexagrams (simplified)
HEXAGRAMS = {
    i: f"Hexagram {i}" for i in range(1, 65)
}

# Human Design Profiles
PROFILES = {
    "1/3": "Investigator/Martyr - Experimental authority, learns through mistakes",
    "1/4": "Investigator/Opportunist - Stable foundation, attracts opportunities",
    "2/4": "Hermit/Opportunist - Withdrawn naturally, attracts through presence",
    "2/5": "Hermit/Heretic - Withdrawn but needed for big things",
    "3/5": "Martyr/Heretic - Learns by trial/error, attracts as solution",
    "3/6": "Martyr/Role Model - Living example, authoritative through experience",
    "4/1": "Opportunist/Investigator - Networks naturally, studies deeply",
    "4/6": "Opportunist/Role Model - Connected, becomes authority naturally",
    "5/1": "Heretic/Investigator - Destined for big impact, needs deep knowledge",
    "5/2": "Heretic/Hermit - Solves problems, works best alone",
    "6/2": "Role Model/Hermit - Influences by example, needs rest/isolation",
    "6/3": "Role Model/Martyr - Guides through experience, learns from trials",
}

# Authority types
AUTHORITIES = {
    "Sacral": "Gut responses - wait for 'mm hmm' or 'uh uh'",
    "Emotional": "Emotional clarity - wait for emotional wave to settle",
    "Splenic": "Instinctual knowing - trust gut instinct in the moment",
    "Ego": "Will power - can initiate and decide consciously",
    "Self-Projected": "Speaking and sensing - reflect on what you say/feel",
    "Lunar": "Wait a lunar cycle (28 days) to see the pattern",
    "No Authority": "Reflectors only - wait a full lunar cycle",
}

# Channels (simplified - 36 main channels)
CHANNELS_DATA = {
    1: {"name": "Self Expression", "theme": "Purpose through action"},
    2: {"name": "Direction", "theme": "Direction of transformation"},
    3: {"name": "Mutation", "theme": "Change and transformation"},
    4: {"name": "Formula", "theme": "Logical process"},
    5: {"name": "Rhythm", "theme": "Timing and rhythm"},
    # ... simplified for demo
}


def calculate_hd_type(birth_time: datetime) -> str:
    """Calculate Human Design Type from birth time."""
    # Simplified calculation based on birth time
    hour = birth_time.hour
    
    # Map hours to types (simplified - real HD uses complex calculations)
    if hour < 6:
        return "Reflector"
    elif hour < 12:
        return "Manifestor"
    elif hour < 18:
        return "Generator"
    else:
        return "Generator Crossing"


def calculate_profile(birth_date: datetime) -> str:
    """Calculate Human Design Profile from birth date."""
    # Simplified: use day of month as profile indicator
    day = birth_date.day % 12
    profile_options = list(PROFILES.keys())
    return profile_options[day % len(profile_options)]


def calculate_authority(birth_time: datetime) -> str:
    """Determine Decision-making Authority."""
    authorities = list(AUTHORITIES.keys())
    hour = birth_time.hour
    return authorities[hour % len(authorities)]


def calculate_channels(birth_date: datetime) -> list:
    """Calculate active channels (simplified)."""
    # Real HD uses planetary positions; this is simplified
    num_channels = 3 + (birth_date.day % 5)
    channels = []
    for i in range(1, num_channels + 1):
        channel_num = (i + birth_date.month) % len(CHANNELS_DATA) or 1
        channels.append({
            "number": channel_num,
            "name": CHANNELS_DATA.get(channel_num, {}).get("name", "Unknown"),
            "theme": CHANNELS_DATA.get(channel_num, {}).get("theme", "Unknown")
        })
    return channels


def generate_hd_chart(
    birth_date: str,
    birth_time: str,
    name: str = "User"
) -> Dict:
    """
    Generate a complete Human Design chart.
    
    Args:
        birth_date: "YYYY-MM-DD"
        birth_time: "HH:MM" (24-hour format)
        name: Person's name
    
    Returns:
        Complete HD chart data
    """
    try:
        # Parse birth data
        bd = datetime.strptime(birth_date, "%Y-%m-%d")
        bt = datetime.strptime(birth_time, "%H:%M")
        
        # Calculate HD elements
        hd_type = calculate_hd_type(bt)
        profile = calculate_profile(bd)
        authority = calculate_authority(bt)
        channels = calculate_channels(bd)
        
        type_info = TYPES.get(hd_type, {})
        profile_info = PROFILES.get(profile, "Unknown profile")
        authority_info = AUTHORITIES.get(authority, "Unknown authority")
        
        chart = {
            "name": name,
            "birth_date": birth_date,
            "birth_time": birth_time,
            "type": {
                "name": hd_type,
                "strategy": type_info.get("strategy", ""),
                "aura": type_info.get("aura", ""),
                "direction": type_info.get("direction", "")
            },
            "profile": {
                "code": profile,
                "description": profile_info
            },
            "authority": {
                "type": authority,
                "description": authority_info
            },
            "channels": channels,
            "summary": f"{name} is a {hd_type} with profile {profile}.\n"
                      f"Strategy: {type_info.get('strategy', 'N/A')}\n"
                      f"Authority: {authority}\n"
                      f"Profile: {profile_info}"
        }
        
        return {"success": True, "chart": chart}
    
    except ValueError as e:
        return {"error": f"Invalid date/time format: {e}"}
    except Exception as e:
        return {"error": str(e)}


def match_compatibility(chart1: Dict, chart2: Dict) -> Dict:
    """
    Compare two Human Design charts for compatibility.
    
    Args:
        chart1: First HD chart (dict)
        chart2: Second HD chart (dict)
    
    Returns:
        Compatibility analysis
    """
    try:
        name1 = chart1.get("name", "Person 1")
        name2 = chart2.get("name", "Person 2")
        
        type1 = chart1.get("type", {}).get("name", "Unknown")
        type2 = chart2.get("type", {}).get("name", "Unknown")
        
        profile1 = chart1.get("profile", {}).get("code", "Unknown")
        profile2 = chart2.get("profile", {}).get("code", "Unknown")
        
        auth1 = chart1.get("authority", {}).get("type", "Unknown")
        auth2 = chart2.get("authority", {}).get("type", "Unknown")
        
        # Simplified compatibility scoring
        compatibility_score = 0
        notes = []
        
        # Type compatibility
        compatible_pairs = {
            "Manifestor-Generator": 0.8,
            "Manifestor-Reflector": 0.6,
            "Generator-Generator": 0.7,
            "Generator-Reflector": 0.8,
            "Reflector-Reflector": 0.5,
        }
        
        pair_key = f"{type1}-{type2}"
        reverse_key = f"{type2}-{type1}"
        type_score = compatible_pairs.get(pair_key) or compatible_pairs.get(reverse_key) or 0.5
        compatibility_score += type_score * 0.3
        
        if type_score > 0.7:
            notes.append(f"[COMPATIBLE] {type1} and {type2} make a compatible pairing")
        else:
            notes.append(f"[CONSIDER] {type1} and {type2} need understanding of differences")
        
        # Authority compatibility
        if auth1 == auth2:
            notes.append(f"[ALIGNED] Shared {auth1} authority - natural alignment")
            compatibility_score += 0.2
        else:
            notes.append(f"[DYNAMIC] Different authorities - can complement or clash")
            compatibility_score += 0.1
        
        # Profile compatibility
        profile_match = 0.6
        if profile1[0] == profile2[0] or profile1[2] == profile2[2]:
            notes.append(f"[RESONANT] Profile similarities: {profile1} & {profile2} share themes")
            profile_match = 0.8
        compatibility_score += profile_match * 0.2
        
        compatibility_score += 0.3  # Base score
        
        compatibility_percent = int(compatibility_score * 100)
        
        return {
            "success": True,
            "pairing": f"{name1} ({type1}) & {name2} ({type2})",
            "compatibility_percent": compatibility_percent,
            "type_compatibility": f"{type1} + {type2}",
            "authority_compatibility": f"{auth1} + {auth2}",
            "profile_compatibility": f"{profile1} + {profile2}",
            "notes": notes,
            "description": " ".join(notes)
        }
    
    except Exception as e:
        return {"error": str(e)}


# Demo
if __name__ == "__main__":
    # Generate sample charts
    chart1 = generate_hd_chart("1990-05-15", "14:30", "Alice")
    chart2 = generate_hd_chart("1992-08-22", "09:15", "Bob")
    
    print("=" * 60)
    print("CHART 1:")
    print(json.dumps(chart1, indent=2))
    
    print("\n" + "=" * 60)
    print("CHART 2:")
    print(json.dumps(chart2, indent=2))
    
    if chart1.get("success") and chart2.get("success"):
        print("\n" + "=" * 60)
        print("COMPATIBILITY:")
        compat = match_compatibility(chart1["chart"], chart2["chart"])
        print(json.dumps(compat, indent=2))
