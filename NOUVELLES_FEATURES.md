# 🚀 Windows MCP - Nouvelles Features (Décembre 2025)

## 📊 Monitoring Système
### `windows_get_temperatures`
- Affiche la température CPU/GPU
- Utilise Open Hardware Monitor ou WMI
### `windows_performance_history`
- Historique CPU/RAM/Disk sur une période
- Export possible en CSV
### `windows_resource_alerts`
- Alertes si seuil CPU/RAM/disk dépassé
---
## 🔒 Sécurité
### `windows_check_updates`
- Liste les mises à jour Windows disponibles
- Option pour installer automatiquement
### `windows_list_drivers`
- Liste tous les pilotes matériels
- Détecte les pilotes obsolètes
### `windows_uac_status`
- Vérifie le statut du Contrôle de Compte d'Utilisateur
---
## 📁 Gestion de Fichiers
### `windows_find_duplicates`
- Trouve les fichiers dupliqués par taille/hachage
- Option de suppression automatique
### `windows_large_files`
- Liste les plus gros fichiers/dossiers
- Filtrage par extension/taille
### `windows_clean_temp`
- Nettoyage des fichiers temporaires
- Mode dry-run pour prévisualisation
---
## 🌐 Réseau
### `windows_speed_test`
- Test de débit upload/download
- Utilise speedtest-cli
### `windows_ping`
- Ping avancé avec statistiques
- Détection de perte de paquets
### `windows_dns_manager`
- Gestion des paramètres DNS
- Flush, changement de serveur
---
## 🎮 Gaming
### `windows_gpu_stats`
- Statistiques GPU en temps réel
- Support NVIDIA/AMD/Intel
### `windows_gaming_processes`
- Liste/ferme les processus liés au gaming
- Détection des overlays (Discord, etc.)
### `windows_steam_games`
- Liste tous les jeux Steam installés
- Parse les fichiers .acf
---
## Installation des dépendances optionnelles
```bash
# Pour speed test
pip install speedtest-cli
# Pour event logs avancés (déjà fait normalement)
pip install pywin32
```
## 🎯 Exemples d'utilisation
```python
# Monitoring
windows_get_temperatures()
windows_performance_history(duration_seconds=60, interval_seconds=5)
windows_resource_alerts(cpu_threshold=80, memory_threshold=80)
# Sécurité
windows_check_updates()
windows_list_drivers()
windows_uac_status()
# Fichiers
windows_find_duplicates(path="C:\\Users\\Stan\\Downloads", min_size_mb=10)
windows_large_files(path="C:\\", top_n=20)
windows_clean_temp(dry_run=True)
# Automation
windows_create_scheduled_task(
    task_name="DailyBackup",
    command="C:\\backup.bat",
    trigger="DAILY",
    start_time="03:00"
)
windows_env_variables(action="get", var_name="PATH")
# Réseau
windows_speed_test()
windows_ping(host="8.8.8.8", count=10)
windows_dns_manager(action="flush")
# Gaming
windows_gpu_stats()
windows_gaming_processes(action="list")
windows_steam_games()
```
---
**Total: 18 nouvelles features ! 🔥**