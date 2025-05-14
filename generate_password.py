from werkzeug.security import generate_password_hash

# Generate password hash for 'admin123'
password = "admin123"
hashed_password = generate_password_hash(password)
print(f"Password hash for '{password}': {hashed_password}")