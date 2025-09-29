#!/usr/bin/env python3
"""
NASA Space Weather System Cleanup Script
Removes redundant files and consolidates functionality
"""

import os
import shutil
from pathlib import Path

def cleanup_redundant_files():
    """Remove redundant files identified in analysis"""
    
    print("NASA SPACE WEATHER SYSTEM CLEANUP")
    print("=" * 50)
    print("Removing redundant files to optimize system...")
    
    # Files to remove (safe removals with no functional impact)
    redundant_files = [
        # Duplicate launchers (keep launch_complete_system.py and launch_simple.py)
        "launch_dashboard.py",
        "start_api.py", 
        "start_expert_dashboard.py",
        "launch_dashboard.bat",
        "start_dashboard_with_api.bat",
        
        # Redundant test files (keep test_ml_ensemble_system.py, quick_forecast_test.py, working_demo.py)
        "quick_test.py",
        "simple_test.py",
        "test_simple_api.py", 
        "test_alternatives.py",
        "simple_email_test.py",
        "test_simple_api_parsing.py",
        
        # Debug/development files
        "debug_dashboard.html",
        "expert_demo.html",
        
        # Additional cleanup
        "simple_backend.py",  # Functionality to be merged into main API
    ]
    
    removed_count = 0
    skipped_count = 0
    
    for file_path in redundant_files:
        full_path = Path(file_path)
        
        if full_path.exists():
            try:
                # Create backup directory if it doesn't exist
                backup_dir = Path("backup_removed_files")
                backup_dir.mkdir(exist_ok=True)
                
                # Backup the file before removal
                backup_path = backup_dir / full_path.name
                shutil.copy2(full_path, backup_path)
                
                # Remove the file
                full_path.unlink()
                print(f"✅ Removed: {file_path} (backed up)")
                removed_count += 1
                
            except Exception as e:
                print(f"❌ Failed to remove {file_path}: {e}")
                skipped_count += 1
        else:
            print(f"⚠️  Not found: {file_path}")
            skipped_count += 1
    
    print("\n" + "=" * 50)
    print("CLEANUP SUMMARY")
    print("=" * 50)
    print(f"Files removed: {removed_count}")
    print(f"Files skipped: {skipped_count}")
    print(f"Files backed up to: backup_removed_files/")
    
    if removed_count > 0:
        print("\n✅ Cleanup completed successfully!")
        print("📁 Redundant files removed and system optimized")
        print("🔄 Backup copies saved in backup_removed_files/")
    
    return removed_count

def verify_core_files():
    """Verify that core files are still present after cleanup"""
    
    print("\n" + "=" * 50)
    print("VERIFYING CORE SYSTEM INTEGRITY")
    print("=" * 50)
    
    core_files = [
        # Core launchers
        "launch_complete_system.py",
        "launch_simple.py",
        
        # Core tests
        "test_ml_ensemble_system.py", 
        "quick_forecast_test.py",
        "working_demo.py",
        
        # Core dashboards
        "expert_dashboard.html",
        "professional_dashboard.html", 
        "3d_dashboard.html",
        "3d_solar_system.html",
        "simple.html",
        "dashboard_hub.html",
        
        # Core backend
        "backend/api_server.py",
        "backend/forecaster.py",
        "backend/expert_forecaster.py",
        "backend/ml_forecaster.py",
        "backend/neural_forecaster.py",
        "backend/ensemble_forecaster.py",
        "backend/nasa_client.py",
        "dashboard_api.py",
    ]
    
    missing_files = []
    present_files = []
    
    for file_path in core_files:
        if Path(file_path).exists():
            present_files.append(file_path)
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} - MISSING!")
    
    print(f"\nCore files present: {len(present_files)}/{len(core_files)}")
    
    if missing_files:
        print(f"\n⚠️  WARNING: {len(missing_files)} core files missing!")
        for file in missing_files:
            print(f"   - {file}")
    else:
        print("\n✅ All core files verified present")
    
    return len(missing_files) == 0

def main():
    """Main cleanup function"""
    try:
        # Verify we're in the right directory
        if not Path("backend").exists() or not Path("expert_dashboard.html").exists():
            print("❌ Error: Not in NASA Space Weather directory")
            print("Please run this script from the NASA project root directory")
            return False
        
        print("🛰️  NASA Space Weather System Optimization")
        print("This will remove redundant files to streamline the system")
        
        # Perform cleanup
        removed_count = cleanup_redundant_files()
        
        # Verify system integrity
        system_intact = verify_core_files()
        
        if system_intact and removed_count > 0:
            print("\n🎯 OPTIMIZATION COMPLETE!")
            print("✅ System streamlined and optimized")
            print("✅ All core functionality preserved") 
            print("🚀 NASA Space Weather System ready for deployment")
            
            # Show next steps
            print("\n📋 NEXT STEPS:")
            print("1. Install missing dependencies: pip install tensorflow openai")
            print("2. Test system: python launch_simple.py")
            print("3. Run comprehensive test: python test_ml_ensemble_system.py")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Cleanup failed - check errors above")
    else:
        print("\n✅ Cleanup completed successfully")