-- 1. Top 10 batsmen by total runs in ODI matches
SELECT batsman, SUM(runs_batted) as total_runs
FROM odi_innings
GROUP BY batsman
ORDER BY total_runs DESC
LIMIT 10;

-- 2. Leading wicket-takers in T20 matches
SELECT bowler, SUM(wicket) as total_wickets
FROM t20_innings
GROUP BY bowler
ORDER BY total_wickets DESC
LIMIT 10;

-- 3. Team with the highest win percentage in Test cricket
WITH team_wins AS (
    SELECT 
        CASE 
            WHEN outcome LIKE '%' || teams || '%' THEN teams
            ELSE NULL 
        END as winning_team,
        COUNT(*) as wins
    FROM test_matches
    GROUP BY winning_team
),
team_matches AS (
    SELECT teams, COUNT(*) as total_matches
    FROM test_matches
    GROUP BY teams
)
SELECT t.teams, 
       COALESCE(w.wins, 0) as wins, 
       t.total_matches,
       ROUND(COALESCE(w.wins, 0) * 100.0 / t.total_matches, 2) as win_percentage
FROM team_matches t
LEFT JOIN team_wins w ON t.teams = w.winning_team
ORDER BY win_percentage DESC
LIMIT 10;

-- 4. Total number of centuries across all match types
SELECT match_type, COUNT(*) as centuries
FROM (
    SELECT match_id, batsman, match_type, SUM(runs_batted) as runs
    FROM (
        SELECT * FROM test_innings
        UNION ALL
        SELECT * FROM odi_innings
        UNION ALL
        SELECT * FROM t20_innings
    ) all_innings
    GROUP BY match_id, batsman, match_type
    HAVING runs >= 100
) centuries
GROUP BY match_type;

-- 5. Matches with the narrowest margin of victory (by runs)
SELECT match_id, teams, outcome
FROM (
    SELECT match_id, teams, outcome,
           CAST(SUBSTR(outcome, 1, INSTR(outcome, ' runs') - 1) AS INTEGER) as margin
    FROM odi_matches
    WHERE outcome LIKE '%runs%'
    UNION ALL
    SELECT match_id, teams, outcome,
           CAST(SUBSTR(outcome, 1, INSTR(outcome, ' runs') - 1) AS INTEGER) as margin
    FROM test_matches
    WHERE outcome LIKE '%runs%'
    UNION ALL
    SELECT match_id, teams, outcome,
           CAST(SUBSTR(outcome, 1, INSTR(outcome, ' runs') - 1) AS INTEGER) as margin
    FROM t20_matches
    WHERE outcome LIKE '%runs%'
) margins
WHERE margin > 0
ORDER BY margin ASC
LIMIT 10;

-- 6. Most economical bowlers in T20 (minimum 50 overs bowled)
SELECT bowler, 
       SUM(total_runs) as total_runs,
       COUNT(DISTINCT match_id || '-' || CAST(over AS TEXT)) as overs,
       ROUND(SUM(total_runs) * 6.0 / COUNT(DISTINCT match_id || '-' || CAST(over AS TEXT)), 2) as economy
FROM t20_innings
GROUP BY bowler
HAVING COUNT(DISTINCT match_id || '-' || CAST(over AS TEXT)) >= 50
ORDER BY economy ASC
LIMIT 10;

-- 7. Batsmen with highest strike rate in ODI (minimum 500 runs)
SELECT batsman,
       SUM(runs_batted) as total_runs,
       COUNT(*) as balls_faced,
       ROUND(SUM(runs_batted) * 100.0 / COUNT(*), 2) as strike_rate
FROM odi_innings
GROUP BY batsman
HAVING SUM(runs_batted) >= 500
ORDER BY strike_rate DESC
LIMIT 10;

-- 8. Teams with most matches won by wickets
SELECT winning_team, COUNT(*) as wins_by_wickets
FROM (
    SELECT 
        CASE 
            WHEN outcome LIKE '%' || teams || '%' THEN teams
            ELSE NULL 
        END as winning_team
    FROM odi_matches
    WHERE outcome LIKE '%wickets%'
    UNION ALL
    SELECT 
        CASE 
            WHEN outcome LIKE '%' || teams || '%' THEN teams
            ELSE NULL 
        END as winning_team
    FROM test_matches
    WHERE outcome LIKE '%wickets%'
    UNION ALL
    SELECT 
        CASE 
            WHEN outcome LIKE '%' || teams || '%' THEN teams
            ELSE NULL 
        END as winning_team
    FROM t20_matches
    WHERE outcome LIKE '%wickets%'
) wins
WHERE winning_team IS NOT NULL
GROUP BY winning_team
ORDER BY wins_by_wickets DESC
LIMIT 10;

-- 9. Most successful venues for each team
SELECT team, venue, COUNT(*) as wins
FROM (
    SELECT 
        CASE 
            WHEN outcome LIKE '%' || teams || '%' THEN 
                CASE 
                    WHEN outcome LIKE '%' || SPLIT(teams, ', ')[1] || '%' THEN SPLIT(teams, ', ')[1]
                    ELSE SPLIT(teams, ', ')[1]
                END
            ELSE NULL 
        END as team,
        venue
    FROM odi_matches
    WHERE outcome NOT LIKE 'tie%' AND outcome NOT LIKE 'no result%'
    UNION ALL
    SELECT 
        CASE 
            WHEN outcome LIKE '%' || teams || '%' THEN 
                CASE 
                    WHEN outcome LIKE '%' || SPLIT(teams, ', ')[1] || '%' THEN SPLIT(teams, ', ')[1]
                    ELSE SPLIT(teams, ', ')[1]
                END
            ELSE NULL 
        END as team,
        venue
    FROM test_matches
    WHERE outcome NOT LIKE 'tie%' AND outcome NOT LIKE 'no result%'
    UNION ALL
    SELECT 
        CASE 
            WHEN outcome LIKE '%' || teams || '%' THEN 
                CASE 
                    WHEN outcome LIKE '%' || SPLIT(teams, ', ')[1] || '%' THEN SPLIT(teams, ', ')[1]
                    ELSE SPLIT(teams, ', ')[1]
                END
            ELSE NULL 
        END as team,
        venue
    FROM t20_matches
    WHERE outcome NOT LIKE 'tie%' AND outcome NOT LIKE 'no result%'
) team_wins
WHERE team IS NOT NULL
GROUP BY team, venue
ORDER BY wins DESC
LIMIT 10;

-- 10. Players with most man of the match awards (if available in data)
-- Note: This would require additional data not typically in cricsheet JSONs

-- 11. Highest individual scores in each format
SELECT match_type, batsman, MAX(runs) as highest_score
FROM (
    SELECT match_id, batsman, match_type, SUM(runs_batted) as runs
    FROM test_innings
    GROUP BY match_id, batsman, match_type
    UNION ALL
    SELECT match_id, batsman, match_type, SUM(runs_batted) as runs
    FROM odi_innings
    GROUP BY match_id, batsman, match_type
    UNION ALL
    SELECT match_id, batsman, match_type, SUM(runs_batted) as runs
    FROM t20_innings
    GROUP BY match_id, batsman, match_type
) individual_scores
GROUP BY match_type
ORDER BY highest_score DESC;

-- 12. Most runs in a calendar year by format
SELECT match_type, year, batsman, total_runs
FROM (
    SELECT match_type, 
           SUBSTR(date, 1, 4) as year,
           batsman,
           SUM(runs_batted) as total_runs,
           RANK() OVER (PARTITION BY match_type, SUBSTR(date, 1, 4) ORDER BY SUM(runs_batted) DESC) as rank
    FROM (
        SELECT ti.*, tm.date
        FROM test_innings ti
        JOIN test_matches tm ON ti.match_id = tm.match_id
        UNION ALL
        SELECT oi.*, om.date
        FROM odi_innings oi
        JOIN odi_matches om ON oi.match_id = om.match_id
        UNION ALL
        SELECT t20i.*, t20m.date
        FROM t20_innings t20i
        JOIN t20_matches t20m ON t20i.match_id = t20m.match_id
    ) all_data
    GROUP BY match_type, year, batsman
) ranked
WHERE rank = 1
ORDER BY match_type, year;

-- 13. Bowlers with best bowling figures in an innings
SELECT match_type, bowler, MAX(wickets) as best_wickets, MIN(runs) as runs
FROM (
    SELECT match_id, bowler, match_type, 
           SUM(wicket) as wickets, 
           SUM(total_runs) as runs
    FROM test_innings
    GROUP BY match_id, bowler, match_type
    HAVING SUM(wicket) >= 5
    UNION ALL
    SELECT match_id, bowler, match_type, 
           SUM(wicket) as wickets, 
           SUM(total_runs) as runs
    FROM odi_innings
    GROUP BY match_id, bowler, match_type
    HAVING SUM(wicket) >= 5
    UNION ALL
    SELECT match_id, bowler, match_type, 
           SUM(wicket) as wickets, 
           SUM(total_runs) as runs
    FROM t20_innings
    GROUP BY match_id, bowler, match_type
    HAVING SUM(wicket) >= 5
) bowling_figures
GROUP BY match_type, bowler
ORDER BY best_wickets DESC, runs ASC
LIMIT 10;

-- 14. Teams with highest success rate when winning toss
SELECT team, 
       SUM(CASE WHEN toss_winner = team AND outcome LIKE '%' || team || '%' THEN 1 ELSE 0 END) as wins_after_toss,
       SUM(CASE WHEN toss_winner = team THEN 1 ELSE 0 END) as toss_wins,
       ROUND(SUM(CASE WHEN toss_winner = team AND outcome LIKE '%' || team || '%' THEN 1 ELSE 0 END) * 100.0 / 
             SUM(CASE WHEN toss_winner = team THEN 1 ELSE 0 END), 2) as win_percentage_after_toss
FROM (
    SELECT teams, 
           CASE 
               WHEN outcome LIKE '%' || SPLIT(teams, ', ')[1] || '%' THEN SPLIT(teams, ', ')[1]
               WHEN outcome LIKE '%' || SPLIT(teams, ', ')[2] || '%' THEN SPLIT(teams, ', ')[2]
               ELSE NULL 
           END as winning_team,
           toss_winner,
           outcome
    FROM odi_matches
    WHERE outcome NOT LIKE 'tie%' AND outcome NOT LIKE 'no result%'
    UNION ALL
    SELECT teams, 
           CASE 
               WHEN outcome LIKE '%' || SPLIT(teams, ', ')[1] || '%' THEN SPLIT(teams, ', ')[1]
               WHEN outcome LIKE '%' || SPLIT(teams, ', ')[2] || '%' THEN SPLIT(teams, ', ')[2]
               ELSE NULL 
           END as winning_team,
           toss_winner,
           outcome
    FROM test_matches
    WHERE outcome NOT LIKE 'tie%' AND outcome NOT LIKE 'no result%'
    UNION ALL
    SELECT teams, 
           CASE 
               WHEN outcome LIKE '%' || SPLIT(teams, ', ')[1] || '%' THEN SPLIT(teams, ', ')[1]
               WHEN outcome LIKE '%' || SPLIT(teams, ', ')[2] || '%' THEN SPLIT(teams, ', ')[2]
               ELSE NULL 
           END as winning_team,
           toss_winner,
           outcome
    FROM t20_matches
    WHERE outcome NOT LIKE 'tie%' AND outcome NOT LIKE 'no result%'
) toss_data
CROSS JOIN (
    SELECT SPLIT(teams, ', ')[1] as team FROM (
        SELECT teams FROM odi_matches
        UNION SELECT teams FROM test_matches
        UNION SELECT teams FROM t20_matches
    )
) teams
WHERE winning_team IS NOT NULL
GROUP BY team
HAVING SUM(CASE WHEN toss_winner = team THEN 1 ELSE 0 END) > 10
ORDER BY win_percentage_after_toss DESC
LIMIT 10;

-- 15. Most productive batting partnerships
SELECT match_type, batsman1, batsman2, AVG(partnership_runs) as avg_partnership
FROM (
    SELECT match_id, match_type, over,
           MIN(batsman) as batsman1,
           MAX(batsman) as batsman2,
           SUM(runs_batted) as partnership_runs
    FROM (
        SELECT match_id, match_type, over, batsman, runs_batted,
               ROW_NUMBER() OVER (PARTITION BY match_id, match_type, over ORDER BY batsman) as rn
        FROM test_innings
        UNION ALL
        SELECT match_id, match_type, over, batsman, runs_batted,
               ROW_NUMBER() OVER (PARTITION BY match_id, match_type, over ORDER BY batsman) as rn
        FROM odi_innings
        UNION ALL
        SELECT match_id, match_type, over, batsman, runs_batted,
               ROW_NUMBER() OVER (PARTITION BY match_id, match_type, over ORDER BY batsman) as rn
        FROM t20_innings
    ) over_data
    WHERE rn <= 2
    GROUP BY match_id, match_type, over
    HAVING COUNT(DISTINCT batsman) = 2
) partnerships
GROUP BY match_type, batsman1, batsman2
HAVING COUNT(*) > 10
ORDER BY avg_partnership DESC
LIMIT 10;

-- 16. Teams with highest average score in first innings
SELECT match_type, team, AVG(innings_total) as avg_first_innings
FROM (
    SELECT match_id, match_type, inning_team as team, SUM(total_runs) as innings_total,
           ROW_NUMBER() OVER (PARTITION BY match_id ORDER BY MIN(over)) as innings_number
    FROM test_innings
    GROUP BY match_id, match_type, inning_team
    UNION ALL
    SELECT match_id, match_type, inning_team as team, SUM(total_runs) as innings_total,
           ROW_NUMBER() OVER (PARTITION BY match_id ORDER BY MIN(over)) as innings_number
    FROM odi_innings
    GROUP BY match_id, match_type, inning_team
    UNION ALL
    SELECT match_id, match_type, inning_team as team, SUM(total_runs) as innings_total,
           ROW_NUMBER() OVER (PARTITION BY match_id ORDER BY MIN(over)) as innings_number
    FROM t20_innings
    GROUP BY match_id, match_type, inning_team
) innings_totals
WHERE innings_number = 1
GROUP BY match_type, team
ORDER BY match_type, avg_first_innings DESC;

-- 17. Most consistent batsmen (lowest standard deviation in scores)
SELECT match_type, batsman, 
       AVG(runs) as avg_runs, 
       STDDEV(runs) as std_dev,
       COUNT(*) as innings
FROM (
    SELECT match_id, batsman, match_type, SUM(runs_batted) as runs
    FROM test_innings
    GROUP BY match_id, batsman, match_type
    UNION ALL
    SELECT match_id, batsman, match_type, SUM(runs_batted) as runs
    FROM odi_innings
    GROUP BY match_id, batsman, match_type
    UNION ALL
    SELECT match_id, batsman, match_type, SUM(runs_batted) as runs
    FROM t20_innings
    GROUP BY match_id, batsman, match_type
) batting_scores
GROUP BY match_type, batsman
HAVING COUNT(*) >= 20
ORDER BY std_dev ASC
LIMIT 10;

-- 18. Powerplay (overs 1-6) performance analysis
SELECT match_type, team,
       AVG(powerplay_runs) as avg_powerplay_runs,
       AVG(powerplay_wickets) as avg_powerplay_wickets
FROM (
    SELECT match_id, match_type, inning_team as team,
           SUM(CASE WHEN over <= 6 THEN total_runs ELSE 0 END) as powerplay_runs,
           SUM(CASE WHEN over <= 6 THEN wicket ELSE 0 END) as powerplay_wickets
    FROM test_innings
    GROUP BY match_id, match_type, inning_team
    UNION ALL
    SELECT match_id, match_type, inning_team as team,
           SUM(CASE WHEN over <= 6 THEN total_runs ELSE 0 END) as powerplay_runs,
           SUM(CASE WHEN over <= 6 THEN wicket ELSE 0 END) as powerplay_wickets
    FROM odi_innings
    GROUP BY match_id, match_type, inning_team
    UNION ALL
    SELECT match_id, match_type, inning_team as team,
           SUM(CASE WHEN over <= 6 THEN total_runs ELSE 0 END) as powerplay_runs,
           SUM(CASE WHEN over <= 6 THEN wicket ELSE 0 END) as powerplay_wickets
    FROM t20_innings
    GROUP BY match_id, match_type, inning_team
) powerplay_data
GROUP BY match_type, team
ORDER BY match_type, avg_powerplay_runs DESC;

-- 19. Death overs (last 5 overs) performance analysis
SELECT match_type, team,
       AVG(death_runs) as avg_death_runs,
       AVG(death_wickets) as avg_death_wickets
FROM (
    SELECT match_id, match_type, inning_team as team,
           SUM(CASE WHEN over >= (SELECT MAX(over) FROM test_innings ti2 WHERE ti2.match_id = ti.match_id) - 4 
                    THEN total_runs ELSE 0 END) as death_runs,
           SUM(CASE WHEN over >= (SELECT MAX(over) FROM test_innings ti2 WHERE ti2.match_id = ti.match_id) - 4 
                    THEN wicket ELSE 0 END) as death_wickets
    FROM test_innings ti
    GROUP BY match_id, match_type, inning_team
    UNION ALL
    SELECT match_id, match_type, inning_team as team,
           SUM(CASE WHEN over >= (SELECT MAX(over) FROM odi_innings oi2 WHERE oi2.match_id = oi.match_id) - 4 
                    THEN total_runs ELSE 0 END) as death_runs,
           SUM(CASE WHEN over >= (SELECT MAX(over) FROM odi_innings oi2 WHERE oi2.match_id = oi.match_id) - 4 
                    THEN wicket ELSE 0 END) as death_wickets
    FROM odi_innings oi
    GROUP BY match_id, match_type, inning_team
    UNION ALL
    SELECT match_id, match_type, inning_team as team,
           SUM(CASE WHEN over >= (SELECT MAX(over) FROM t20_innings t20i2 WHERE t20i2.match_id = t20i.match_id) - 4 
                    THEN total_runs ELSE 0 END) as death_runs,
           SUM(CASE WHEN over >= (SELECT MAX(over) FROM t20_innings t20i2 WHERE t20i2.match_id = t20i.match_id) - 4 
                    THEN wicket ELSE 0 END) as death_wickets
    FROM t20_innings t20i
    GROUP BY match_id, match_type, inning_team
) death_data
GROUP BY match_type, team
ORDER BY match_type, avg_death_runs DESC;

-- 20. Player performance across all formats
SELECT player, 
       SUM(CASE WHEN match_type = 'test' THEN runs ELSE 0 END) as test_runs,
       SUM(CASE WHEN match_type = 'odi' THEN runs ELSE 0 END) as odi_runs,
       SUM(CASE WHEN match_type = 't20' THEN runs ELSE 0 END) as t20_runs,
       SUM(runs) as total_runs,
       SUM(CASE WHEN match_type = 'test' THEN wickets ELSE 0 END) as test_wickets,
       SUM(CASE WHEN match_type = 'odi' THEN wickets ELSE 0 END) as odi_wickets,
       SUM(CASE WHEN match_type = 't20' THEN wickets ELSE 0 END) as t20_wickets,
       SUM(wickets) as total_wickets
FROM (
    -- Batting performance
    SELECT batsman as player, match_type, SUM(runs_batted) as runs, 0 as wickets
    FROM test_innings
    GROUP BY batsman, match_type
    UNION ALL
    SELECT batsman as player, match_type, SUM(runs_batted) as runs, 0 as wickets
    FROM odi_innings
    GROUP BY batsman, match_type
    UNION ALL
    SELECT batsman as player, match_type, SUM(runs_batted) as runs, 0 as wickets
    FROM t20_innings
    GROUP BY batsman, match_type
    
    UNION ALL
    
    -- Bowling performance
    SELECT bowler as player, match_type, 0 as runs, SUM(wicket) as wickets
    FROM test_innings
    GROUP BY bowler, match_type
    UNION ALL
    SELECT bowler as player, match_type, 0 as runs, SUM(wicket) as wickets
    FROM odi_innings
    GROUP BY bowler, match_type
    UNION ALL
    SELECT bowler as player, match_type, 0 as runs, SUM(wicket) as wickets
    FROM t20_innings
    GROUP BY bowler, match_type
) player_performance
GROUP BY player
HAVING total_runs > 1000 OR total_wickets > 50
ORDER BY total_runs + total_wickets * 20 DESC
LIMIT 20;