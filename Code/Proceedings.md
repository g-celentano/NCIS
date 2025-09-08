# Proceedings: Modular SDN Controller Implementation

## Obiettivo

Progettare e implementare un controller SDN modulare basato su Ryu, compatibile con Mininet, in grado di monitorare il traffico, rilevare anomalie con soglie adattive e applicare blocchi granulari e sblocchi progressivi. Il controller deve essere estendibile e offrire un'interfaccia REST per la gestione dinamica delle policy.

---

## Struttura dei Moduli

### 1. controller.py
- **Responsabilità:** Orchestrazione dei moduli, gestione degli eventi OpenFlow, avvio dei thread di monitoraggio, detection, mitigazione e API REST.
- **Motivazione:** Separare la logica SDN dalla logica di monitoraggio, detection e mitigazione per favorire la manutenibilità e l'estendibilità.
- **Migliorie:** Gestione della lista degli switch (`dps`), avvio thread per lo sblocco progressivo.

### 2. monitor.py
- **Responsabilità:** Raccolta periodica delle statistiche di porta, MAC, IP e protocollo dagli switch.
- **Motivazione:** Fornire dati granulari e aggiornati per la detection e la mitigazione. Thread-safe per evitare race condition.
- **Funzionalità:** Calcolo del throughput per MAC, IP, protocollo; funzione `get_stats` per accesso ai dati.

### 3. detector.py
- **Responsabilità:** Analisi delle statistiche tramite plugin, rilevamento di anomalie con soglie adattive (media mobile, deviazione standard).
- **Motivazione:** Modularità e facilità di estensione con nuove strategie di detection. Thread dedicato per analisi continua.
- **Funzionalità:** Notifica delle anomalie al mitigator tramite callback.

### 4. mitigator.py
- **Responsabilità:** Applicazione di regole di blocco/sblocco granulari (MAC/IP/UDP port), gestione dello sblocco progressivo, coordinamento delle decisioni collaborative.
- **Motivazione:** Evitare overblocking, garantire la sicurezza e la flessibilità operativa. Permettere contributi da moduli esterni alle decisioni di sicurezza.
- **Funzionalità:** Blocco automatico su segnalazione del detector, gestione thread-safe dei flussi bloccati, shared blocklist e external policies per decisioni collaborative.

### 5. api.py
- **Responsabilità:** Esporre endpoint REST per la gestione dinamica delle regole di blocco/sblocco e delle policy collaborative.
- **Motivazione:** Permettere l'integrazione con applicazioni esterne e la modifica runtime delle policy. Supportare decisioni collaborative da moduli esterni.
- **Funzionalità:** Endpoint per bloccare, sbloccare e visualizzare lo stato dei flussi bloccati. Gestione policy esterne e shared blocklist.

### 6. external_security_module.py
- **Responsabilità:** Esempio di modulo esterno che contribuisce alle decisioni di blocco tramite threat intelligence e policy amministrative.
- **Motivazione:** Dimostrare l'estendibilità del sistema e la capacità di integrazione con sistemi di sicurezza esterni.
- **Funzionalità:** Threat intelligence, policy automatiche, interfaccia di emergenza per amministratori.

---

## Motivazioni delle Scelte
- **Modularità:** Ogni responsabilità è separata in un modulo dedicato, facilitando test, estensioni e manutenzione.
- **Threading:** Utilizzato per monitoraggio continuo, detection e sblocco progressivo, garantendo reattività e aggiornamento costante.
- **Soglie adattive:** Permettono di rilevare anomalie in modo robusto e dinamico, riducendo i falsi positivi.
- **Blocco granulare:** Minimizza l'impatto sul traffico legittimo, intervenendo solo sui flussi sospetti.
- **Sblocco progressivo:** Penalizza i flussi recidivi, favorendo la resilienza della rete.
- **Decisioni collaborative:** Permette a moduli esterni, sistemi di threat intelligence e amministratori di contribuire alle policy di sicurezza.
- **REST API:** Consente la gestione runtime delle policy, favorendo l'integrazione con sistemi esterni e la gestione collaborativa.
- **Logging:** Traccia tutte le decisioni per audit e debug.

---

## Estendibilità
- **Detection plugin-based:** Nuove strategie di detection possono essere aggiunte facilmente.
- **Mitigator:** Può essere esteso per supportare altri criteri di blocco/sblocco.
- **API:** Endpoint REST facilmente ampliabili.
- **Collaborative Blocking:** Sistema aperto per integrare moduli esterni di sicurezza, threat intelligence e policy amministrative.

---

## Implementazione Collaborative Blocking Decisions

### Problema Risolto
- **Flaw:** Solo il controller prendeva decisioni di blocco, limitando l'estendibilità.
- **Soluzione:** Implementata struttura dati condivisa per blocklist e policy esterne.

### Componenti Aggiunti
- **Shared Blocklist:** Repository centralizzato per decisioni di blocco da fonti multiple
- **External Policies:** Regole pattern-based da moduli esterni
- **REST API estesa:** Endpoint per gestione policy collaborative
- **External Security Module:** Esempio di integrazione con threat intelligence

### Benefici
- **Estendibilità:** Facile integrazione di nuovi moduli di sicurezza
- **Flessibilità:** Decisioni di blocco da controller, admin, e sistemi esterni
- **Responsività:** Aggiornamento policy in tempo reale
- **Trasparenza:** Tutte le policy sono loggate e auditable

---

## Stato finale
Tutti i file sono stati implementati secondo le specifiche richieste, inclusa la nuova funzionalità di Collaborative Blocking Decisions. La soluzione è pronta per essere testata e ulteriormente estesa secondo le necessità future. Il sistema ora supporta decisioni di sicurezza collaborative, superando il limite del controller-centric blocking.
