import csv
import random
from typing import List, Dict, Set, Tuple
from collections import defaultdict


def parseCsv(filename: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse the CSV file and return songs with performers.
    
    Returns:
        Tuple of (regular_songs, guest_performances)
    """
    songs = []
    guest_performances = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
                
            song_info = row[0].strip()
            performers = [p.strip() for p in row[1:] if p.strip()]
            
            song_dict = {
                'name': song_info,
                'performers': set(performers)
            }
            
            # Check if it's a guest performance
            if performers == ['Guest Performer']:
                guest_performances.append(song_dict)
            else:
                songs.append(song_dict)
    
    return songs, guest_performances


def calculate_overlap(song1: Dict, song2: Dict) -> int:
    """Calculate the number of overlapping performers between two songs."""
    return len(song1['performers'].intersection(song2['performers']))


def calculate_setlist_score(setlist: List[Dict]) -> float:
    """
    Calculate a score for the setlist. Higher is better.
    Score is based on minimizing performer overlap between consecutive and nearby songs.
    """
    score = 0.0
    
    for i in range(len(setlist)):
        for j in range(i + 1, min(i + 4, len(setlist))):  # Look at next 3 songs
            overlap = calculate_overlap(setlist[i], setlist[j])
            distance = j - i
            # Penalize overlap more heavily for songs that are closer together
            penalty = overlap * (4 - distance) * 10
            score -= penalty
    
    return score


def find_best_position_for_song(partial_setlist: List[Dict], song: Dict, 
                                 start_idx: int, end_idx: int) -> int:
    """
    Find the best position to insert a song in the setlist to minimize overlap.
    """
    best_score = float('-inf')
    best_position = start_idx
    
    for pos in range(start_idx, end_idx + 1):
        # Try inserting at this position
        test_list = partial_setlist[:pos] + [song] + partial_setlist[pos:]
        # Only score the relevant section
        section_to_score = test_list[max(0, pos-3):min(len(test_list), pos+4)]
        score = calculate_setlist_score(section_to_score)
        
        if score > best_score:
            best_score = score
            best_position = pos
    
    return best_position


def generateSetlist(songs: List[Dict], guest_performances: List[Dict], 
                   iterations: int = 1000) -> List[List[Dict]]:
    """
    Generate an optimal setlist with the given constraints.
    
    Constraints:
    1. Bouncy and This World must be at the end (joint performance)
    2. Structure: 3 groups of 5, 1 group of 6 (total 21 songs)
    3. Guest performers can be placed anywhere
    
    Returns:
        List of 4 groups (sets) of songs
    """
    # Find the ending songs
    bouncy = next((s for s in songs if 'Bouncy' in s['name']), None)
    this_world = next((s for s in songs if 'This World' in s['name']), None)
    
    if not bouncy or not this_world:
        raise ValueError("Bouncy and This World must be in the song list")
    
    # Remove ending songs from the pool
    available_songs = [s for s in songs if s not in [bouncy, this_world]]
    
    # Total songs needed: 21 (5+5+5+6)
    # We have 2 ending songs, need 19 more (can include 4 guest performers)
    total_needed = 19
    
    best_setlist = None
    best_score = float('-inf')
    
    for iteration in range(iterations):
        # Shuffle available songs for this iteration
        shuffled = available_songs.copy()
        random.shuffle(shuffled)
        
        # Build setlist greedily with some randomness
        setlist = []
        remaining = shuffled.copy()
        
        # Add songs one by one, finding good positions
        while len(setlist) < total_needed and remaining:
            song = remaining.pop(0)
            
            if len(setlist) == 0:
                setlist.append(song)
            else:
                # Find best position for this song
                pos = find_best_position_for_song(setlist, song, 0, len(setlist))
                setlist.insert(pos, song)
        
        # Add guest performances if we need more songs
        guest_idx = 0
        while len(setlist) < total_needed and guest_idx < len(guest_performances):
            # Guest performances can go anywhere, distribute them evenly
            ideal_pos = (len(setlist) * (guest_idx + 1)) // (len(guest_performances) + 1)
            setlist.insert(ideal_pos, guest_performances[guest_idx])
            guest_idx += 1
        
        # Add the ending songs
        setlist.extend([bouncy, this_world])
        
        # Calculate score for this setlist
        score = calculate_setlist_score(setlist)
        
        if score > best_score:
            best_score = score
            best_setlist = setlist.copy()
    
    # Split into groups: [5, 5, 5, 6]
    groups = [
        best_setlist[0:5],
        best_setlist[5:10],
        best_setlist[10:15],
        best_setlist[15:21]
    ]
    
    return groups


def print_setlist(groups: List[List[Dict]]):
    """Print the setlist in a readable format."""
    set_names = ["Set 1 (Before 1st Intermission)", 
                 "Set 2 (After 1st Intermission)",
                 "Set 3 (Before 2nd Intermission)", 
                 "Set 4 (Finale)"]
    
    print("\n" + "="*70)
    print("GENERATED SETLIST")
    print("="*70)
    
    for idx, (set_name, group) in enumerate(zip(set_names, groups), 1):
        print(f"\n{set_name}:")
        print("-" * 70)
        for i, song in enumerate(group, 1):
            performers = ", ".join(sorted(song['performers'])) if song['performers'] != {'Guest Performer'} else "Guest Performer"
            print(f"  {i}. {song['name']}")
            print(f"     Performers: {performers}")
        
        if idx < len(groups):
            print(f"\n{'⭐ INTERMISSION ⭐':^70}")
    
    print("\n" + "="*70)
    
    # Print statistics
    print("\nSETLIST STATISTICS:")
    print("-" * 70)
    all_songs = [song for group in groups for song in group]
    
    # Count performer appearances and gaps
    performer_positions = defaultdict(list)
    for pos, song in enumerate(all_songs):
        for performer in song['performers']:
            if performer != 'Guest Performer':
                performer_positions[performer].append(pos)
    
    print(f"\nTotal Songs: {len(all_songs)}")
    print(f"Total Performers: {len(performer_positions)}")
    
    # Calculate minimum gaps between performances
    print("\nPerformers with shortest gaps between performances:")
    gaps = []
    for performer, positions in performer_positions.items():
        if len(positions) > 1:
            min_gap = min(positions[i+1] - positions[i] for i in range(len(positions)-1))
            gaps.append((performer, min_gap, len(positions)))
    
    gaps.sort(key=lambda x: x[1])
    for performer, min_gap, num_songs in gaps[:10]:
        print(f"  {performer}: {num_songs} songs, minimum gap = {min_gap}")


def main():
    csv_filename = 'SetList.csv'
    
    print("Parsing songs from CSV...")
    songs, guest_performances = parseCsv(csv_filename)
    
    print(f"Found {len(songs)} regular songs and {len(guest_performances)} guest performances")
    
    print("\nGenerating optimal setlist...")
    print("(This may take a moment as we optimize performer separation...)")
    
    groups = generateSetlist(songs, guest_performances, iterations=1000)
    
    print_setlist(groups)


if __name__ == "__main__":
    main()