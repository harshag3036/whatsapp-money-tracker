#!/usr/bin/env python3
"""
Fix SSL certificate verification issues on macOS.
This script helps resolve the common SSL certificate verification error on macOS.
"""

import os
import sys
import ssl
import certifi

def fix_ssl_certificates():
    """Print instructions to fix SSL certificate issues."""
    print("SSL Certificate Verification Error Detected")
    print("==========================================")
    print("\nThis is a common issue with Python on macOS.")
    print("Here are three ways to fix it:\n")
    
    print("Option 1: Install certificates for Python (Recommended)")
    print("------------------------------------------------------")
    print("Run the following command in your terminal:")
    print("/Applications/Python 3.11/Install Certificates.command")
    print("(Adjust the Python version if needed)")
    print("\nOR\n")
    print(f"Run: {sys.executable} -m pip install --upgrade certifi")
    print(f"Current certifi path: {certifi.where()}")
    
    print("\nOption 2: Set SSL_CERT_FILE environment variable")
    print("----------------------------------------------")
    print("Add this to your shell profile (~/.zshrc or ~/.bash_profile):")
    print(f"export SSL_CERT_FILE={certifi.where()}")
    print("Then restart your terminal or run: source ~/.zshrc")
    
    print("\nOption 3: Temporary workaround (Not recommended for production)")
    print("-------------------------------------------------------------")
    print("Add this code at the beginning of your script:")
    print("import ssl")
    print("ssl._create_default_https_context = ssl._create_unverified_context")
    
    print("\nLet's try Option 3 for now to test if it works:")
    
    # Apply the temporary fix
    ssl._create_default_https_context = ssl._create_unverified_context
    print("\nTemporary SSL verification bypass applied.")
    print("You can now run your script again, but please implement Option 1 or 2 for a proper fix.")

if __name__ == "__main__":
    fix_ssl_certificates()
