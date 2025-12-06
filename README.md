# 🖥️ Windows MCP
**Un outil modulaire pour automatiser, surveiller et optimiser Windows via PowerShell et Python.**

---

## 📋 Description
`windows_mcp` est un **Micro Command Processor** (MCP) conçu pour étendre les capacités de gestion système sous Windows.
Il permet d'automatiser des tâches, surveiller les ressources, gérer les fichiers, le réseau, et même optimiser les performances gaming — le tout via une API simple ou en ligne de commande.

---

## ✨ Fonctionnalités
### 📊 **Monitoring Système**
- `windows_get_temperatures()` : Températures CPU/GPU.
- `windows_performance_history()` : Historique des ressources.
- `windows_resource_alerts()` : Alertes personnalisables.

### 🔒 **Sécurité**
- `windows_check_updates()` : Mises à jour Windows.
- `windows_uac_status()` : Statut du UAC.
- `windows_list_drivers()` : Pilotes obsolètes.

### 📁 **Gestion de Fichiers**
- `windows_find_duplicates()` : Nettoyage des doublons.
- `windows_large_files()` : Identification des gros fichiers.
- `windows_clean_temp()` : Nettoyage des fichiers temporaires.

### 🌐 **Réseau**
- `windows_speed_test()` : Test de débit.
- `windows_ping()` : Diagnostics réseau.
- `windows_dns_manager()` : Gestion du DNS.

### 🎮 **Gaming**
- `windows_gpu_stats()` : Statistiques GPU.
- `windows_steam_games()` : Liste des jeux Steam.

### ⚙️ **Automatisation**
- `windows_create_scheduled_task()` : Planification de tâches.
- `windows_run_script()` : Exécution de scripts (.bat, .ps1).
- `windows_env_variables()` : Gestion des variables d'environnement.

*(Voir [NOUVELLES_FEATURES.md](NOUVELLES_FEATURES.md) pour la liste complète.)*

---

## 🛠️ Installation
### Prérequis
- Python 3.8+
- PowerShell 5.1+ (pour certaines fonctionnalités)

### Étapes
1. Cloner le dépôt :
   ```bash
   git clone https://github.com/powershelling/windows_mcp.git
   cd windows_mcp
   ```
2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
   *(Si `requirements.txt` n'existe pas, installer manuellement : `pip install speedtest-cli pywin32`.)*

3. Lancer le serveur :
   ```bash
   python main.py
   ```

---

## 🚀 Utilisation
### Exemple 1 : Surveillance des ressources
```python
from server_instance import mcp
mcp.windows_get_temperatures()
mcp.windows_resource_alerts(cpu_threshold=80)
```

### Exemple 2 : Nettoyage de fichiers
```python
mcp.windows_clean_temp(dry_run=True)  # Mode simulation
mcp.windows_find_duplicates(path="C:\\Downloads", min_size_mb=10)
```

### Exemple 3 : Automatisation
```python
mcp.windows_create_scheduled_task(
    task_name="Backup",
    command="C:\\backup.bat",
    trigger="DAILY",
    start_time="03:00"
)
```

---

## 📄 Licence
Projet sous licence **MIT** – libre à l'usage, modification et distribution.
*(Voir [LICENSE](LICENSE) pour plus de détails.)*

---

## 🤝 Contribution
Les pull requests sont les bienvenues !
Pour les bugs ou suggestions, ouvrir une [issue](https://github.com/powershelling/windows_mcp/issues).