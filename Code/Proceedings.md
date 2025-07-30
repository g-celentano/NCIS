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
- **Responsabilità:** Applicazione di regole di blocco/sblocco granulari (MAC/IP/UDP port), gestione dello sblocco progressivo, logging delle decisioni.
- **Motivazione:** Evitare overblocking, garantire la sicurezza e la flessibilità operativa. Thread dedicato per lo sblocco automatico.
- **Funzionalità:** Blocco automatico su segnalazione del detector, gestione thread-safe dei flussi bloccati.

### 5. api.py
- **Responsabilità:** Esporre endpoint REST per la gestione dinamica delle regole di blocco/sblocco.
- **Motivazione:** Permettere l'integrazione con applicazioni esterne e la modifica runtime delle policy.
- **Funzionalità:** Endpoint per bloccare, sbloccare e visualizzare lo stato dei flussi bloccati.

---

## Motivazioni delle Scelte
- **Modularità:** Ogni responsabilità è separata in un modulo dedicato, facilitando test, estensioni e manutenzione.
- **Threading:** Utilizzato per monitoraggio continuo, detection e sblocco progressivo, garantendo reattività e aggiornamento costante.
- **Soglie adattive:** Permettono di rilevare anomalie in modo robusto e dinamico, riducendo i falsi positivi.
- **Blocco granulare:** Minimizza l'impatto sul traffico legittimo, intervenendo solo sui flussi sospetti.
- **Sblocco progressivo:** Penalizza i flussi recidivi, favorendo la resilienza della rete.
- **REST API:** Consente la gestione runtime delle policy, favorendo l'integrazione con sistemi esterni.
- **Logging:** Traccia tutte le decisioni per audit e debug.

---

## Estendibilità
- **Detection plugin-based:** Nuove strategie di detection possono essere aggiunte facilmente.
- **Mitigator:** Può essere esteso per supportare altri criteri di blocco/sblocco.
- **API:** Endpoint REST facilmente ampliabili.

---

## Stato finale
Tutti i file sono stati implementati secondo le specifiche richieste. La soluzione è pronta per essere testata e ulteriormente estesa secondo le necessità future.
