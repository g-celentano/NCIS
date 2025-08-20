# Tesina Progetto SDN – Firewall e Mitigazione DoS

## STEP DA SEGUIRE

1. **Introduzione**
   - Spiega il contesto delle reti SDN e il problema DoS/DDoS.
   - Motiva la necessità di correggere i flaw principali.

2. **Presentazione dei flaw del progetto precedente**
   - Elenca e descrivi sinteticamente i difetti riscontrati (solo quelli che poi andrai a correggere).

3. **Obiettivi della nuova soluzione**
   - Esplicita quali flaw vengono affrontati e perché sono prioritari.

4. **Descrizione tecnica delle correzioni**
   - Per ogni flaw (3 obbligatori + 2 opzionali), dedica una sottosezione:
     - Spiega il problema (come era prima).
     - Descrivi la soluzione adottata.
     - Mostra il funzionamento nel codice (snippet e spiegazione).
     - Argomenta i vantaggi ottenuti.

5. **API REST**
   - Spiega il ruolo delle API REST nella gestione del firewall.
   - Illustra le principali chiamate e come permettono la gestione runtime delle policy.
   - Mostra esempi di utilizzo e output.

6. **Risultati sperimentali**
   - Sintetizza le prove fatte per validare le correzioni (setup di test, comportamenti osservati).
   - Mostra come le modifiche hanno effettivamente migliorato la situazione rispetto al passato.

7. **Conclusioni**
   - Riepiloga i punti chiave e i vantaggi concreti della nuova soluzione.
   - Eventuali prospettive di miglioramento future (solo se attinenti ai flaw trattati).

---

## SCALLETTA DEGLI ARGOMENTI

1. **Introduzione**
   - SDN e vulnerabilità DoS/DDoS
   - Necessità di evolvere il firewall

2. **Flaw principali del progetto precedente**
   - Over blocking
   - Static threshold
   - Lack of modular detection/mitigation
   - (Opzionali scelti) Detection limitata a DoS classici
   - (Opzionali scelti) Inflexible blocking/unblocking policy

3. **Obiettivi e criteri di correzione**
   - Elenco dei flaw affrontati e ragioni della scelta

4. **Correzione dei flaw**
   - **Over blocking**
     - Problema
     - Soluzione a livello di flusso/host (MAC/IP), gestione blocklist/whitelist
     - Vantaggi
   - **Static threshold**
     - Problema
     - Soglie adattive implementate (media mobile, rate history)
     - Vantaggi
   - **Modular detection/mitigation**
     - Problema
     - Separazione in moduli (controller, monitor, detector, mitigator), threading
     - Vantaggi
   - **Detection su pattern avanzati**
     - Problema (solo flood riconosciuti)
     - Soluzione (detection burst, rate spike, SYN flood)
     - Vantaggi
   - **Policy di blocco/sblocco flessibile**
     - Problema (sblocco troppo rigido o permissivo)
     - Soluzione (sblocco progressivo, backoff dinamico)
     - Vantaggi

5. **API REST**
   - Motivazione e ruolo
   - Descrizione endpoint principali
   - Esempi di chiamata e output
   - Come favoriscono la gestione runtime

6. **Validazione sperimentale**
   - Setup di test e metodologia
   - Risultati osservati per i flaw corretti

7. **Conclusioni**
   - Sintesi dei miglioramenti concreti
   - Breve cenno a possibili estensioni future correlate ai flaw trattati
