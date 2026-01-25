@echo off
REM Phase 2 Full Experiment - Terminal Mode
REM Runs all 180 configurations with live terminal output

echo ================================================================================
echo SKYT PHASE 2 FULL EXPERIMENT - TERMINAL MODE
echo ================================================================================
echo Contracts: 12
echo Models: 3 (gpt-4o-mini, gpt-4o, claude-sonnet-4-5-20250929)
echo Temperatures: 5 (0.0, 0.3, 0.5, 0.7, 1.0)
echo Runs per config: 20
echo Total configurations: 180
echo Total generations: 3600
echo ================================================================================
echo.

set CONTRACTS=fibonacci_basic fibonacci_recursive slugify balanced_brackets gcd binary_search lru_cache merge_sort quick_sort factorial is_palindrome is_prime
set MODELS=gpt-4o-mini gpt-4o claude-sonnet-4-5-20250929
set TEMPS=0.0 0.3 0.5 0.7 1.0

set /a CONFIG_NUM=0
set /a TOTAL_CONFIGS=180

for %%C in (%CONTRACTS%) do (
    echo.
    echo ================================================================================
    echo CONTRACT: %%C
    echo ================================================================================
    
    for %%M in (%MODELS%) do (
        echo.
        echo   MODEL: %%M
        echo   ----------------------------------------------------------------------------
        
        for %%T in (%TEMPS%) do (
            set /a CONFIG_NUM+=1
            
            echo.
            echo     [!CONFIG_NUM!/%TOTAL_CONFIGS%] Temperature %%T - Running 20 generations...
            
            python main.py --contract %%C --runs 20 --temperature %%T --model %%M
            
            if errorlevel 1 (
                echo.
                echo     ERROR: Experiment failed! Stopping.
                echo ================================================================================
                exit /b 1
            )
            
            echo     COMPLETED
        )
    )
)

echo.
echo ================================================================================
echo PHASE 2 COMPLETE - ALL 180 CONFIGURATIONS FINISHED
echo ================================================================================
echo Results saved to: outputs/
echo Metrics summary: outputs/metrics_summary.csv
echo ================================================================================
