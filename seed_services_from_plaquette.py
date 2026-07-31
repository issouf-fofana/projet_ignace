"""Remplace les Services existants par les 12 services de la plaquette
CISO-as-a-Service (code, fonction, livrables, valeur ajoutée).

Usage :
    python seed_services_from_plaquette.py
"""
from app import app
from models import db, Service

SERVICES = [
    dict(
        code="EPP-01", function_tag="Protéger · Détecter",
        title="Sécurité des Endpoints",
        description="Protection managée du parc de terminaux : déploiement, supervision et administration continue de l'EDR/XDR, durcissement des configurations et réponse aux incidents postes.",
        deliverables="Console EDR/XDR opérée 24/7, politiques réglées sur votre exposition métier.\nRapport mensuel de posture endpoint (couverture, incidents, délais de remédiation).\nPlaybooks de confinement et d'isolation des postes compromis.",
        value_text="Détection et confinement des menaces sur le poste réduits à quelques minutes, sans mobiliser d'expertise interne rare.",
    ),
    dict(
        code="IAM-02", function_tag="Protéger",
        title="Gestion des Identités & Accès",
        description="Gouvernance externalisée des identités : provisioning/déprovisioning, MFA, revues d'accès et rationalisation des privilèges sur tout le cycle de vie des comptes.",
        deliverables="Cartographie des identités et matrice des droits (privilèges, services, comptes dormants).\nCampagnes de revue d'accès périodiques avec attestation formalisée.\nTableau de bord IAM (couverture MFA, comptes orphelins, écarts SoD).",
        value_text="Surface d'attaque liée aux identités réduite et exigences d'accès des référentiels satisfaites, preuves à l'appui.",
    ),
    dict(
        code="VMS-03", function_tag="Identifier",
        title="Gestion des Vulnérabilités",
        description="Cycle continu de scan, priorisation contextualisée (criticité métier × exploitabilité), suivi de remédiation et vérification de correction sur tout le périmètre.",
        deliverables="Scans récurrents interne/externe, rapport priorisé par risque réel — pas par CVSS brut.\nPlan de remédiation avec SLA de correction par niveau de criticité.\nIndicateurs de tendance (délai moyen, taux de récurrence, backlog).",
        value_text="Un flux ingérable de vulnérabilités transformé en plan d'action priorisé et mesurable, aligné sur l'appétence au risque.",
    ),
    dict(
        code="NET-04", function_tag="Protéger",
        title="Sécurité Réseau",
        description="Conception, supervision et administration du filtrage et de la segmentation (pare-feu, VLAN, NAC, IDS/IPS), durcissement des équipements et contrôle des flux inter-zones.",
        deliverables="Architecture de segmentation documentée et matrice des flux autorisés.\nRevue périodique des règles (nettoyage, règles obsolètes, shadow rules).\nRapport de détection réseau (intrusions, flux anormaux, mouvements latéraux).",
        value_text="Propagation latérale limitée en cas de compromission et flux maîtrisés de façon démontrable — socle d'une architecture Zero Trust.",
    ),
    dict(
        code="DAT-05", function_tag="Protéger",
        title="Sécurité des Données",
        description="Protection du cycle de vie de la donnée : classification, chiffrement, DLP et contrôle des accès, en cohérence avec les obligations réglementaires.",
        deliverables="Schéma de classification et cartographie des données sensibles.\nPolitique de chiffrement et de gestion des clés opérationnalisée.\nRapport DLP (tentatives d'exfiltration, canaux à risque, incidents qualifiés).",
        value_text="Risque de fuite et de sanction réduit, avec une visibilité claire sur où sont vos données critiques et qui y accède.",
    ),
    dict(
        code="AWR-06", function_tag="Protéger · Facteur humain",
        title="Sensibilisation & Formation",
        description="Programme continu d'acculturation cyber : phishing simulé, e-learning ciblé par population et formations dédiées aux profils à risque (dirigeants, IT, financiers).",
        deliverables="Plan annuel segmenté par population et niveau de risque.\nCampagnes de phishing simulé avec analyse comportementale et taux de clic.\nTableau de bord de maturité humaine (progression, risque résiduel).",
        value_text="Le vecteur n°1 des compromissions traité avec des métriques d'évolution exploitables pour piloter et démontrer le risque.",
    ),
    dict(
        code="BCK-07", function_tag="Récupérer",
        title="Sauvegarde & Restauration",
        description="Sauvegardes managées selon une stratégie résiliente (3-2-1, immuabilité, isolement anti-ransomware) avec tests de restauration réguliers.",
        deliverables="Politique de sauvegarde formalisée (RPO/RTO par actif, rétention, immuabilité).\nRapports de succès/échec et supervision continue.\nTests de restauration documentés avec preuve de reprise effective.",
        value_text="Une reprise réelle et non théorique face au ransomware — la différence entre une sauvegarde qui existe et une qui restaure.",
    ),
    dict(
        code="PEN-08", function_tag="Identifier",
        title="Test d'Intrusion",
        description="Campagnes de pentest à la demande ou récurrentes (externe, interne, web, applicatif, ingénierie sociale) avec restitution actionnable et suivi de remédiation.",
        deliverables="Rapport hiérarchisé (impact métier, exploitabilité, preuve d'exploitation).\nPlan de remédiation priorisé et restitution technique.\nRetest post-remédiation attestant de la correction.",
        value_text="L'efficacité réelle de vos défenses validée par la mise à l'épreuve offensive, au-delà de la conformité déclarative.",
    ),
    dict(
        code="AIS-09", function_tag="Protéger · Émergent",
        title="Sécurité des Écosystèmes IA",
        description="Sécurisation des usages et déploiements IA/LLM : gouvernance des données, protection contre les attaques spécifiques (prompt injection, empoisonnement) et encadrement du Shadow AI.",
        deliverables="Cartographie des usages IA (officiels et Shadow AI) et risques associés.\nPolitique d'usage sécurisé de l'IA et garde-fous techniques (filtrage, DLP prompts).\nRapport de posture IA (surface d'exposition, dépendances, écarts).",
        value_text="Un risque émergent encore peu couvert maîtrisé : adopter l'IA en avantage compétitif sans ouvrir de nouvelle brèche.",
    ),
    dict(
        code="SOC-10", function_tag="Détecter · Répondre",
        title="SOC-as-a-Service",
        description="Détection et réponse aux incidents 24/7 via SIEM/SOAR opéré, corrélation d'événements, threat intelligence et prise en charge de bout en bout des alertes qualifiées.",
        deliverables="Supervision continue, use cases alignés sur votre exposition et MITRE ATT&CK.\nRapports d'incidents qualifiés (chronologie, impact, actions de réponse).\nReporting mensuel (volumétrie, MTTD/MTTR, top menaces, recommandations).",
        value_text="Une capacité de détection de niveau entreprise sans le coût d'un SOC interne, avec des délais mesurés et contractualisés.",
    ),
    dict(
        code="GRC-11", function_tag="Gouverner",
        title="Gouvernance, Risque & Conformité",
        description="Pilotage externalisé du SMSI : gestion documentaire, analyse et traitement des risques, suivi des plans de conformité et préparation aux audits et certifications.",
        deliverables="Analyse de risques tenue à jour et plan de traitement suivi.\nCorpus documentaire (politiques, procédures) maintenu et versionné.\nTableau de bord de conformité multi-référentiel et registre des preuves.",
        value_text="Un niveau de conformité permanent et non ponctuel : l'audit devient une simple formalité de restitution.",
    ),
    dict(
        code="MAT-12", function_tag="Identifier · Gouverner",
        title="Audit & Maturité Sécurité SI",
        description="Évaluation objective et périodique de la posture (gap analysis, scoring par domaine) et feuille de route priorisée par le risque et le ROI sécurité.",
        deliverables="Rapport de maturité par domaine (échelle niveau 1 à 5) et analyse des écarts.\nFeuille de route priorisée (quick wins vs chantiers structurants).\nSynthèse exécutive COMEX (exposition au risque, investissements, KPI).",
        value_text="Une vision chiffrée du niveau de sécurité réel pour arbitrer les investissements et démontrer la progression dans le temps.",
    ),
]

with app.app_context():
    deleted = Service.query.delete()
    print(f"{deleted} ancien(s) service(s) supprimé(s).")

    for position, data in enumerate(SERVICES, start=1):
        db.session.add(Service(position=position, **data))

    db.session.commit()
    print(f"{len(SERVICES)} services créés.")

print("Terminé.")
