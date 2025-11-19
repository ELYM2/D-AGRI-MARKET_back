import requests
import json

BASE_URL = "http://localhost:8000/api"

def get_token(username, password):
    response = requests.post(f"{BASE_URL}/auth/login/", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access"]
    print(f"Login failed for {username}: {response.status_code} - {response.text}")
    return None

def create_user(username, email, password):
    response = requests.post(f"{BASE_URL}/auth/register/", json={
        "username": username,
        "email": email,
        "password": password
    })
    if response.status_code != 201:
        print(f"Create user failed for {username}: {response.status_code} - {response.text}")

def test_messaging():
    print("📧 TEST DE LA MESSAGERIE")
    print("=" * 50)

    # 1. Création des utilisateurs de test
    print("\n1. Création des utilisateurs...")
    # Utilisation de suffixes aléatoires ou juste des noms nouveaux pour éviter les conflits
    import random
    suffix = random.randint(1000, 9999)
    acheteur = f"acheteur_{suffix}"
    vendeur = f"vendeur_{suffix}"
    
    create_user(acheteur, f"{acheteur}@test.com", "password123")
    create_user(vendeur, f"{vendeur}@test.com", "password123")

    # 2. Connexion
    print("2. Connexion...")
    token_acheteur = get_token(acheteur, "password123")
    token_vendeur = get_token(vendeur, "password123")
    
    if not token_acheteur or not token_vendeur:
        print("❌ Erreur de connexion")
        return

    # Récupérer l'ID du vendeur
    headers_vendeur = {"Authorization": f"Bearer {token_vendeur}"}
    resp = requests.get(f"{BASE_URL}/auth/me/", headers=headers_vendeur)
    vendeur_id = resp.json()["id"]

    # 3. Envoi d'un message (Acheteur -> Vendeur)
    print("\n3. Envoi d'un message (Acheteur -> Vendeur)...")
    headers_acheteur = {"Authorization": f"Bearer {token_acheteur}"}
    msg_data = {
        "receiver": vendeur_id,
        "subject": "Question sur les tomates",
        "body": "Bonjour, vos tomates sont-elles bio ?"
    }
    
    resp = requests.post(f"{BASE_URL}/messages/", json=msg_data, headers=headers_acheteur)
    if resp.status_code == 201:
        print("✅ Message envoyé avec succès")
        print(json.dumps(resp.json(), indent=2))
        msg_id = resp.json()["id"]
    else:
        print(f"❌ Erreur d'envoi: {resp.status_code}")
        print(resp.text)
        return

    # 4. Vérification de la réception (Vendeur)
    print("\n4. Vérification de la boîte de réception (Vendeur)...")
    resp = requests.get(f"{BASE_URL}/messages/?box=inbox", headers=headers_vendeur)
    messages = resp.json().get('results', [])
    
    found = False
    for m in messages:
        if m["id"] == msg_id:
            print("✅ Message bien reçu dans l'inbox")
            print(f"   Sujet: {m['subject']}")
            print(f"   De: {m['sender_name']}")
            found = True
            break
    
    if not found:
        print("❌ Message non trouvé dans l'inbox")

    # 5. Marquer comme lu
    print("\n5. Marquer le message comme lu...")
    resp = requests.post(f"{BASE_URL}/messages/{msg_id}/mark_read/", headers=headers_vendeur)
    if resp.status_code == 200:
        print("✅ Message marqué comme lu")
    else:
        print(f"❌ Erreur: {resp.status_code}")

    print("\n✨ Test de messagerie terminé !")

if __name__ == "__main__":
    test_messaging()
