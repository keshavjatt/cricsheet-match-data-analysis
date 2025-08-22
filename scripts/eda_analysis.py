# eda_analysis.py (UPDATED VERSION - New Database Structure)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup visualization style
plt.style.use('ggplot')
sns.set_palette("husl")

# Database connection from .env file 
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/cricsheet.db')  # Default fallback
engine = create_engine(DATABASE_URL)
print(f"Using database: {DATABASE_URL}")  # Debug info

def load_data_from_db():
    """Database se data load karta hai - NEW VERSION"""
    print("Loading data from database...")
    
    # Naye tables se data load karo
    all_matches = pd.read_sql('SELECT * FROM matches', engine)
    all_innings = pd.read_sql('SELECT * FROM innings', engine)
    
    # Ab humein alag format ke data filter karna hoga
    test_matches = all_matches[all_matches['match_type'].str.contains('test', case=False, na=False)]
    odi_matches = all_matches[all_matches['match_type'].str.contains('odi', case=False, na=False)]
    t20_matches = all_matches[all_matches['match_type'].str.contains('t20', case=False, na=False)]
    
    test_innings = all_innings[all_innings['match_id'].isin(test_matches['match_id'])]
    odi_innings = all_innings[all_innings['match_id'].isin(odi_matches['match_id'])]
    t20_innings = all_innings[all_innings['match_id'].isin(t20_matches['match_id'])]
    
    return all_matches, all_innings, test_matches, odi_matches, t20_matches, test_innings, odi_innings, t20_innings

def create_visualizations():
    """10 different visualizations banata hai - UPDATED VERSION"""
    print("Creating visualizations...")
    
    # Data load karo
    all_matches, all_innings, test_matches, odi_matches, t20_matches, test_innings, odi_innings, t20_innings = load_data_from_db()
    
    # Output directory banayo
    os.makedirs('presentation', exist_ok=True)
    
    # Check if we have enough data
    if len(all_matches) == 0 or len(all_innings) == 0:
        print("❌ ERROR: No data found in database!")
        print("Please run sql_manager.py first to load data")
        return
    
    print(f"📊 Found {len(all_matches)} matches and {len(all_innings)} innings records")
    
    # 1. Match Distribution by Type (Pie Chart)
    plt.figure(figsize=(10, 8))
    match_counts = all_matches['match_type'].value_counts()
    
    if len(match_counts) > 0:
        plt.pie(match_counts.values, labels=match_counts.index, autopct='%1.1f%%')
        plt.title('Distribution of Matches by Format')
        plt.savefig('presentation/1_match_distribution.png', bbox_inches='tight')
        plt.close()
        print("✓ Created Match Distribution Chart")
    else:
        print("⚠️  Not enough data for Match Distribution Chart")
    
    # 2. Top 10 Batsmen by Runs (Bar Chart)
    if len(all_innings) > 0:
        plt.figure(figsize=(12, 8))
        top_batsmen = all_innings.groupby('batsman')['runs_batted'].sum().nlargest(10)
        
        if len(top_batsmen) > 0:
            plt.barh(top_batsmen.index, top_batsmen.values)
            plt.xlabel('Total Runs')
            plt.title('Top 10 Batsmen by Total Runs')
            plt.gca().invert_yaxis()
            plt.savefig('presentation/2_top_batsmen.png', bbox_inches='tight')
            plt.close()
            print("✓ Created Top Batsmen Chart")
        else:
            print("⚠️  Not enough data for Top Batsmen Chart")
    
    # 3. Top 10 Bowlers by Wickets (Bar Chart)
    if len(all_innings) > 0:
        plt.figure(figsize=(12, 8))
        top_bowlers = all_innings.groupby('bowler')['wicket'].sum().nlargest(10)
        
        if len(top_bowlers) > 0:
            plt.barh(top_bowlers.index, top_bowlers.values)
            plt.xlabel('Total Wickets')
            plt.title('Top 10 Bowlers by Total Wickets')
            plt.gca().invert_yaxis()
            plt.savefig('presentation/3_top_bowlers.png', bbox_inches='tight')
            plt.close()
            print("✓ Created Top Bowlers Chart")
        else:
            print("⚠️  Not enough data for Top Bowlers Chart")
    
    # 4. Runs Distribution by Match Type (Box Plot)
    if len(all_innings) > 0 and len(all_matches) > 0:
        plt.figure(figsize=(12, 8))
        match_runs = all_innings.groupby(['match_id', 'match_type'])['total_runs'].sum().reset_index()
        
        if len(match_runs) > 0:
            sns.boxplot(x='match_type', y='total_runs', data=match_runs)
            plt.title('Total Runs Distribution by Match Format')
            plt.xlabel('Match Format')
            plt.ylabel('Total Runs')
            plt.savefig('presentation/4_runs_distribution.png', bbox_inches='tight')
            plt.close()
            print("✓ Created Runs Distribution Chart")
        else:
            print("⚠️  Not enough data for Runs Distribution Chart")
    
    # 5. Win Percentage by Toss Decision
    if len(all_matches) > 0:
        plt.figure(figsize=(12, 8))
        
        # Toss analysis
        toss_analysis = all_matches[all_matches['winner'].notna()]
        if len(toss_analysis) > 0:
            toss_analysis['toss_winner_won'] = toss_analysis.apply(
                lambda x: 1 if x['toss_winner'] == x['winner'] else 0, axis=1)
            
            toss_result = toss_analysis.groupby('toss_decision')['toss_winner_won'].value_counts().unstack().fillna(0)
            if len(toss_result) > 0:
                toss_result_percentage = toss_result.div(toss_result.sum(axis=1), axis=0) * 100
                toss_result_percentage.plot(kind='bar', stacked=True)
                plt.title('Win Percentage by Toss Decision')
                plt.xlabel('Toss Decision')
                plt.ylabel('Percentage')
                plt.legend(['Lost', 'Won'])
                plt.savefig('presentation/5_toss_analysis.png', bbox_inches='tight')
                plt.close()
                print("✓ Created Toss Analysis Chart")
            else:
                print("⚠️  Not enough data for Toss Analysis Chart")
        else:
            print("⚠️  Not enough data for Toss Analysis Chart")
    
    # 6. Run Rate Over Time (Line Chart)
    if len(odi_matches) > 0 and len(odi_innings) > 0:
        plt.figure(figsize=(12, 8))
        
        try:
            odi_matches_copy = odi_matches.copy()
            odi_matches_copy['date'] = pd.to_datetime(odi_matches_copy['date'], errors='coerce')
            odi_matches_copy = odi_matches_copy.dropna(subset=['date'])
            odi_matches_copy['year'] = odi_matches_copy['date'].dt.year

            odi_innings_with_year = odi_innings.merge(
                odi_matches_copy[['match_id', 'year']], on='match_id', how='left')
            odi_innings_with_year = odi_innings_with_year.dropna(subset=['year'])

            yearly_stats = odi_innings_with_year.groupby('year').agg(
                total_runs=('total_runs', 'sum'),
                total_balls=('over', 'count')
            ).reset_index()

            yearly_stats['run_rate'] = yearly_stats['total_runs'] / (yearly_stats['total_balls'] / 6) if yearly_stats['total_balls'].sum() > 0 else 0

            plt.plot(yearly_stats['year'], yearly_stats['run_rate'], marker='o', linewidth=2, markersize=6)
            plt.title('Average Run Rate in ODI Matches Over Time')
            plt.xlabel('Year')
            plt.ylabel('Run Rate')
            plt.grid(True, alpha=0.3)
            plt.savefig('presentation/6_odi_run_rate.png', bbox_inches='tight')
            plt.close()
            print("✓ Created Run Rate Chart")
        except:
            print("⚠️  Error creating Run Rate Chart")
    
    # 7. Player Performance Across Formats (Heatmap)
    if len(all_innings) > 0:
        plt.figure(figsize=(14, 10))
        
        try:
            batting_perf = all_innings.groupby('batsman')['runs_batted'].sum().reset_index()
            bowling_perf = all_innings.groupby('bowler')['wicket'].sum().reset_index()
            
            all_rounders = pd.merge(batting_perf, bowling_perf, left_on='batsman', right_on='bowler', how='inner')
            if len(all_rounders) > 0:
                all_rounders = all_rounders[(all_rounders['runs_batted'] > 100) & (all_rounders['wicket'] > 5)]  # Threshold kam kiya
                top_all_rounders = all_rounders.nlargest(5, 'runs_batted')['batsman'].tolist()  # Top 5 hi
                
                format_performance = []
                for player in top_all_rounders:
                    player_data = {
                        'Player': player,
                        'Test Runs': all_innings[(all_innings['batsman'] == player) & (all_innings['match_type'].str.contains('test', case=False))]['runs_batted'].sum(),
                        'ODI Runs': all_innings[(all_innings['batsman'] == player) & (all_innings['match_type'].str.contains('odi', case=False))]['runs_batted'].sum(),
                        'T20 Runs': all_innings[(all_innings['batsman'] == player) & (all_innings['match_type'].str.contains('t20', case=False))]['runs_batted'].sum(),
                    }
                    format_performance.append(player_data)
                
                perf_df = pd.DataFrame(format_performance).set_index('Player')
                sns.heatmap(perf_df, annot=True, fmt='.0f', cmap='YlOrRd')
                plt.title('Top All-rounders Batting Performance Across Formats')
                plt.savefig('presentation/7_all_rounders_heatmap.png', bbox_inches='tight')
                plt.close()
                print("✓ Created All-rounders Heatmap")
            else:
                print("⚠️  Not enough data for All-rounders Heatmap")
        except:
            print("⚠️  Error creating All-rounders Heatmap")
    
    # 8. Match Results by Venue (Bar Chart)
    if len(all_matches) > 0:
        plt.figure(figsize=(14, 8))
        
        try:
            venue_results = all_matches['venue'].value_counts().head(10).index
            venue_data = all_matches[all_matches['venue'].isin(venue_results)]
            
            venue_wins = venue_data.groupby('venue')['winner'].value_counts().unstack().fillna(0)
            venue_wins.head(10).plot(kind='bar', stacked=True, figsize=(14, 8))
            plt.title('Match Wins by Top Venues')
            plt.xlabel('Venue')
            plt.ylabel('Number of Wins')
            plt.legend(title='Team', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig('presentation/8_venue_analysis.png', bbox_inches='tight')
            plt.close()
            print("✓ Created Venue Analysis Chart")
        except:
            print("⚠️  Error creating Venue Analysis Chart")
    
    # 9. Player Career Progression (Line Chart)
    if len(all_innings) > 0 and len(all_matches) > 0:
        plt.figure(figsize=(14, 8))
        
        try:
            # Top player select karo
            top_players = all_innings.groupby('batsman')['runs_batted'].sum().nlargest(3).index
            
            for i, top_player in enumerate(top_players):
                player_data = all_innings[all_innings['batsman'] == top_player]
                player_matches = player_data.merge(all_matches[['match_id', 'date']], on='match_id')
                player_matches['date'] = pd.to_datetime(player_matches['date'], errors='coerce')
                player_matches = player_matches.dropna(subset=['date'])
                player_matches = player_matches.sort_values('date')
                player_matches['cumulative_runs'] = player_matches['runs_batted'].cumsum()
                player_matches['match_num'] = range(1, len(player_matches) + 1)
                
                plt.plot(player_matches['match_num'], player_matches['cumulative_runs'], linewidth=2, label=top_player)
            
            plt.title('Career Progression of Top Batsmen')
            plt.xlabel('Match Number')
            plt.ylabel('Cumulative Runs')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig('presentation/9_career_progression.png', bbox_inches='tight')
            plt.close()
            print("✓ Created Career Progression Chart")
        except:
            print("⚠️  Error creating Career Progression Chart")
    
    # 10. Average Runs per Over by Format (Bar Chart)
    if len(all_innings) > 0:
        plt.figure(figsize=(12, 8))
        
        try:
            format_run_rates = []
            for fmt in all_innings['match_type'].unique():
                fmt_data = all_innings[all_innings['match_type'] == fmt]
                total_runs = fmt_data['total_runs'].sum()
                total_overs = fmt_data['over'].nunique()
                run_rate = total_runs / total_overs if total_overs > 0 else 0
                format_run_rates.append({'Format': fmt, 'Run_Rate': run_rate})
            
            run_rate_df = pd.DataFrame(format_run_rates)
            plt.bar(run_rate_df['Format'], run_rate_df['Run_Rate'])
            plt.title('Average Runs per Over by Format')
            plt.xlabel('Format')
            plt.ylabel('Runs per Over')
            plt.savefig('presentation/10_run_rate_by_format.png', bbox_inches='tight')
            plt.close()
            print("✓ Created Run Rate by Format Chart")
        except:
            print("⚠️  Error creating Run Rate by Format Chart")
    
    print("\n✅ All visualizations completed!")
    print("Check the 'presentation' folder for all charts and graphs!")

if __name__ == "__main__":
    create_visualizations()