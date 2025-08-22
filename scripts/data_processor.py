import os
import json
import pandas as pd
import numpy as np
from glob import glob
from tqdm import tqdm
import multiprocessing as mp
from functools import partial
import time

def load_json_files():
    """Saari JSON files load karta hai"""
    json_files = glob('data/raw/*.json')[:100]  # ONLY FIRST 100 FILES
    print(f"Processing {len(json_files)} JSON files")
    return json_files

def parse_single_file(json_file):
    """Single JSON file process karta hai"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic match info
        match_info = data['info']
        match_id = os.path.basename(json_file).replace('.json', '')
        
        # Match type detection
        match_type = match_info.get('match_type', 'unknown')
        if match_type == 'unknown':
            if 'event' in match_info:
                event_name = match_info.get('event', {}).get('name', '').lower()
                if 'test' in event_name:
                    match_type = 'test'
                elif 'odi' in event_name or 'one day' in event_name:
                    match_type = 'odi'
                elif 't20' in event_name or 'twenty' in event_name:
                    match_type = 't20'
                elif 'ipl' in event_name:
                    match_type = 'ipl'
        
        # Teams
        teams = match_info.get('teams', ['Unknown', 'Unknown'])
        
        # Match summary
        match_summary = {
            'match_id': match_id,
            'match_type': match_type,
            'team1': teams[0] if len(teams) > 0 else 'Unknown',
            'team2': teams[1] if len(teams) > 1 else 'Unknown',
            'venue': match_info.get('venue', 'Unknown'),
            'date': match_info.get('dates', ['Unknown'])[0],
            'winner': match_info.get('outcome', {}).get('winner', 'Unknown'),
            'toss_winner': match_info.get('toss', {}).get('winner', 'Unknown'),
            'toss_decision': match_info.get('toss', {}).get('decision', 'Unknown')
        }
        
        # Innings data - ONLY IF INNINGS EXISTS
        innings_data = []
        if 'innings' in data:
            for inning in data['innings']:
                team = inning['team']
                
                for over_num, over in enumerate(inning['overs'], 1):
                    for delivery_num, delivery in enumerate(over['deliveries'], 1):
                        runs = delivery['runs']
                        
                        innings_data.append({
                            'match_id': match_id,
                            'match_type': match_type,
                            'inning_team': team,
                            'over': over_num,
                            'ball': delivery_num,
                            'batsman': delivery['batter'],
                            'bowler': delivery['bowler'],
                            'runs_batted': runs['batter'],
                            'extras': runs['extras'],
                            'total_runs': runs['total'],
                            'wicket': 1 if 'wickets' in delivery else 0
                        })
        
        return pd.DataFrame(innings_data), pd.DataFrame([match_summary])
        
    except Exception as e:
        print(f"Error processing {json_file}: {str(e)[:100]}...")
        return pd.DataFrame(), pd.DataFrame()

def process_files_sequentially(json_files):
    """Sequential processing - Multiprocessing se better for small data"""
    print("Processing files sequentially for better performance...")
    
    all_innings = pd.DataFrame()
    all_matches = pd.DataFrame()
    
    for json_file in tqdm(json_files, desc="Processing JSON files"):
        innings_df, match_df = parse_single_file(json_file)
        
        if not innings_df.empty:
            all_innings = pd.concat([all_innings, innings_df], ignore_index=True)
        if not match_df.empty:
            all_matches = pd.concat([all_matches, match_df], ignore_index=True)
    
    return all_innings, all_matches

def process_all_data():
    """Saari JSON files process karta hai"""
    json_files = load_json_files()
    
    if len(json_files) == 0:
        print("Koi JSON files nahi mili! Pehle scraper.py run karo.")
        return
    
    # SEQUENTIAL PROCESSING - Faster for small datasets
    start_time = time.time()
    all_innings, all_matches = process_files_sequentially(json_files)
    end_time = time.time()
    
    print(f"Processing completed in {end_time - start_time:.2f} seconds")
    
    # Check if we have data
    if all_innings.empty or all_matches.empty:
        print("Koi data nahi mila. JSON structure check karo.")
        return
    
    # Data ko match type ke hisaab se alag karo
    for match_type in all_matches['match_type'].unique():
        if match_type != 'unknown':
            # Matches filter karo
            type_matches = all_matches[all_matches['match_type'] == match_type]
            type_innings = all_innings[all_innings['match_id'].isin(type_matches['match_id'])]
            
            # CSV save karo
            type_matches.to_csv(f'data/processed/{match_type}_matches.csv', index=False)
            type_innings.to_csv(f'data/processed/{match_type}_innings.csv', index=False)
    
    # Data summary print karo
    print("\n📊 Data Processing Summary:")
    print(f"Total Matches Processed: {len(all_matches)}")
    print(f"Total Ball-by-Ball Records: {len(all_innings):,}")
    
    for match_type in all_matches['match_type'].unique():
        count = len(all_matches[all_matches['match_type'] == match_type])
        print(f"{match_type.upper()} Matches: {count}")

if __name__ == "__main__":
    # Output directory banayo
    os.makedirs('data/processed', exist_ok=True)
    
    # Data process karo
    process_all_data()