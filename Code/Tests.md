# Tests.md

## Scenari da simulare

### 1. Topologia semplice (topology.py)
- **Obiettivo:** Verificare che il controller distingua tra traffico DoS e traffico legittimo.
- **Setup:** 3 host (h1, h2, h3), 4 switch.
- **Simulazioni:**
  - h1 → h3: traffico DoS (es. flood UDP/TCP)
  - h2 → h3: traffico legittimo (es. ping, iperf)

### 2. Topologia complessa (topology_new.py)
- **Obiettivo:** Dimostrare l’indipendenza dalla topologia e la scalabilità del controller.
- **Setup:** 7 host (h1-h7), 10 switch, mesh/tree-like.
- **Simulazioni:**
  - h1-h4 → h7: traffico DoS distribuito (multi-attacker)
  - h5/h6 → h7: traffico legittimo
  - Test di traffico tra host su switch diversi

---

## Passi generali per la simulazione

1. **Avvia il controller**
   ```bash
   ryu-manager controller.py
   ```

2. **Avvia la topologia desiderata**
   - Semplice:
     ```bash
     sudo python3 topology.py
     ```
   - Complessa:
     ```bash
     sudo python3 topology_new.py
     ```

3. **Genera traffico DoS**
   - Esempio UDP flood:
     ```bash
     mininet> h1 ping h3
     mininet> h1 nping --udp -c 10000 -p 12345 h3
     mininet> h1 hping3 -S -p 80 --flood h3
     ```
   - Per topologia complessa:
     ```bash
     mininet> h1 hping3 --flood h7
     mininet> h2 hping3 --flood h7
     mininet> h3 hping3 --flood h7
     mininet> h4 hping3 --flood h7
     ```

4. **Genera traffico legittimo**
   - Esempio:
     ```bash
     mininet> h2 ping h3
     mininet> h2 iperf -c h3
     mininet> h5 ping h7
     mininet> h6 iperf -c h7
     ```

5. **Verifica il comportamento**
   - Controlla i log del controller per:
     - Rilevazione anomalie
     - Applicazione blocchi granulari
     - Sblocco progressivo
     - Logging delle decisioni
   - Usa l’API REST per visualizzare e gestire i flussi bloccati:
     ```bash
     curl http://localhost:5000/blocked
     ```

6. **Testa la resilienza**
   - Prova a far ripartire il traffico legittimo dopo lo sblocco.
   - Verifica che solo i flussi sospetti vengano bloccati.

---

## Suggerimenti

- Modifica la topologia e ripeti i test per dimostrare la modularità e l’indipendenza dalla struttura di rete.
- Varia la quantità e la tipologia di traffico per testare la sensibilità del detector.
- Prova a inserire/rimuovere regole manualmente tramite l’API REST.