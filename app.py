import math
import hashlib
import requests
import re
import json
from flask import Flask, render_template, request, jsonify, Response

app = Flask(__name__)

def calculate_shannon_entropy(password):
    if not password:
        return 0.0, 0
    char_counts = {}
    for char in password:
        char_counts[char] = char_counts.get(char, 0) + 1
    
    entropy = 0.0
    length = len(password)
    for count in char_counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
    
    total_entropy_bits = round(entropy * length, 2)
    return total_entropy_bits, length

def estimate_crack_time(entropy_bits):
    if entropy_bits <= 0:
        return "Instantaneous (< 1 second)", "Critical"
    
    guesses_per_sec = 1e11 # 100 Billion guesses/sec (Enterprise GPU Cluster)
    total_combinations = 2 ** entropy_bits
    seconds = total_combinations / (2 * guesses_per_sec)
    
    if seconds < 1:
        return "Instantaneous (< 1 second)", "Critical"
    elif seconds < 60:
        return f"~{int(seconds)} seconds", "High Risk"
    elif seconds < 3600:
        return f"~{int(seconds / 60)} minutes", "Moderate"
    elif seconds < 86400:
        return f"~{int(seconds / 3600)} hours", "Moderate"
    elif seconds < 31536000:
        return f"~{int(seconds / 86400)} days", "Safe"
    elif seconds < 31536000 * 100:
        return f"~{int(seconds / 31536000)} years", "Secure"
    else:
        return "Centuries (Computationally Secure)", "Enterprise Grade"

def check_hibp_breach(password):
    sha1_pwd = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1_pwd[:5], sha1_pwd[5:]
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            for line in response.text.splitlines():
                h, count = line.split(':')
                if h == suffix:
                    return int(count)
        return 0
    except Exception:
        return 0

def simulate_kdf_inspection(password):
    if not password:
        return {"salt": "0000000000000000", "iterations": 0, "cost": "N/A"}
    salt = hashlib.sha256(password.encode()).hexdigest()[:16].upper()
    return {
        "salt": salt,
        "algorithm": "Argon2id / PBKDF2-HMAC-SHA512",
        "iterations": 600000,
        "memoryCost": "64 MiB",
        "parallelism": "4 Threads"
    }

def audit_12_policies(password):
    if not password:
        password = ""
    
    policies = {
        "len_12": len(password) >= 12,
        "len_16": len(password) >= 16,
        "upper": bool(re.search(r'[A-Z]', password)),
        "lower": bool(re.search(r'[a-z]', password)),
        "numeric": bool(re.search(r'\d', password)),
        "symbol": bool(re.search(r'[^A-Za-z0-9]', password)),
        "no_repeating": not bool(re.search(r'(.)\1{2,}', password)),
        "no_sequential": not bool(re.search(r'(123|abc|qwe|xyz|password|admin)', password, re.IGNORECASE)),
        "mixed_case": bool(re.search(r'[A-Z]', password)) and bool(re.search(r'[a-z]', password)),
        "multi_symbol": len(re.findall(r'[^A-Za-z0-9]', password)) >= 2,
        "entropy_check": calculate_shannon_entropy(password)[0] >= 60.0,
        "not_breached": check_hibp_breach(password) == 0 if password else True
    }
    return policies

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/audit', methods=['POST'])
def audit():
    data = request.get_json()
    password = data.get('password', '')
    
    entropy, length = calculate_shannon_entropy(password)
    crack_time, risk_level = estimate_crack_time(entropy)
    breach_count = check_hibp_breach(password)
    policies = audit_12_policies(password)
    kdf_data = simulate_kdf_inspection(password)
    
    passed_count = sum(1 for v in policies.values() if v)

    return jsonify({
        'length': length,
        'entropy': entropy,
        'crackTime': crack_time,
        'riskLevel': risk_level,
        'breachCount': breach_count,
        'policies': policies,
        'passedCount': passed_count,
        'kdf': kdf_data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)