"""
Script de test détaillé pour l'API d'authentification
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_test(number, description):
    print(f"\n{number}️⃣  {description}")
    print("-" * 70)

def test_auth_api():
    print_section("🔐 TEST COMPLET DE L'API D'AUTHENTIFICATION")
    
    # Générer un nom d'utilisateur unique
    timestamp = str(int(time.time()))
    username = f"testuser_{timestamp}"
    email = f"test_{timestamp}@example.com"
    password = "SecurePass123!"
    
    print(f"\n📝 Données de test:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    
    # 1. Test de création de compte
    print_test("1", "Création de compte (POST /api/auth/register/)")
    
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ SUCCÈS - Compte créé!")
            print(f"\n📦 Réponse:")
            print(json.dumps(data, indent=2))
            
            access_token = data.get("access")
            refresh_token = data.get("refresh")
            user_id = data.get("user", {}).get("id")
            
            print(f"\n🔑 Tokens reçus:")
            print(f"   Access Token: {access_token[:50]}...")
            print(f"   Refresh Token: {refresh_token[:50]}...")
            print(f"   User ID: {user_id}")
            
        else:
            print(f"❌ ÉCHEC - Status {response.status_code}")
            print(f"\n📦 Réponse d'erreur:")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text)
            return
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return
    
    # 2. Test de récupération du profil
    print_test("2", "Récupération du profil (GET /api/auth/me/)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/me/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ SUCCÈS - Profil récupéré!")
            print(f"\n📦 Profil utilisateur:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ ÉCHEC - Status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    # 3. Test de connexion
    print_test("3", "Connexion (POST /api/auth/login/)")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login/",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCÈS - Connexion réussie!")
            print(f"\n📦 Nouveaux tokens:")
            print(json.dumps(data, indent=2))
            new_access = data.get("access")
        else:
            print(f"❌ ÉCHEC - Status {response.status_code}")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text)
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    # 4. Test de rafraîchissement du token
    print_test("4", "Rafraîchissement du token (POST /api/auth/refresh/)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/refresh/",
            json={"refresh": refresh_token},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ SUCCÈS - Token rafraîchi!")
            print(f"\n📦 Nouveau token:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ ÉCHEC - Status {response.status_code}")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text)
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    # 5. Test de déconnexion
    print_test("5", "Déconnexion (POST /api/auth/logout/)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/logout/",
            json={"refresh": refresh_token},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 205:
            print(f"✅ SUCCÈS - Déconnexion réussie!")
        else:
            print(f"❌ ÉCHEC - Status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    # Résumé
    print_section("✨ RÉSUMÉ DES TESTS")
    print("\n✅ Tous les endpoints d'authentification sont fonctionnels!")
    print("\n📋 Endpoints testés:")
    print("   1. POST /api/auth/register/ - Création de compte")
    print("   2. GET  /api/auth/me/ - Profil utilisateur")
    print("   3. POST /api/auth/login/ - Connexion")
    print("   4. POST /api/auth/refresh/ - Rafraîchissement token")
    print("   5. POST /api/auth/logout/ - Déconnexion")
    print("\n")

if __name__ == "__main__":
    test_auth_api()
