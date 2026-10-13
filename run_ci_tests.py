import unittest
import sys
import os

if __name__ == '__main__':
    # Tests papkasini avtomat kashf qilish
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        print("\n" + "="*70)
        print("CI TEST FAILURE SUMMARY:")
        print("="*70)
        for test, trace in result.failures:
            print(f"\n[FAIL] {test}:")
            print(trace)
        for test, trace in result.errors:
            print(f"\n[ERROR] {test}:")
            print(trace)
        sys.exit(1)
    else:
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY ON CI RUNNER!")
        sys.exit(0)
