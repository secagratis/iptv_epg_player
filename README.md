==================================================
        MANUALE VELOCE - IPTV SUITE ALL-IN-ONE
==================================================

1. AVVIO DEL PROGRAMMA
--------------------------------------------------
- Avvia  (o lo script python iptv_suite_all_in_one.py).
- Si aprira' una finestra di controllo desktop e in automatico il lettore Web nel browser (http://127.0.0.1:18888).
- NOTA IMPORTANTE: Non chiudere la finestra di controllo desktop mentre guardi i canali, serve a mantenere attivo il proxy locale anti-CORS in background.

2. CARICAMENTO E RIPRODUZIONE CANALI
--------------------------------------------------
- Nel primo campo in alto a sinistra, inserisci l'URL di una playlist .m3u o di un singolo stream .m3u8 (es. https://jmp2.uk/plu-...).
- Per caricare un file locale dal PC: clicca su "File M3U".
- Clicca su "Carica M3U / Stream".
- Usa il campo "Cerca canale..." o il filtro "Gruppo" per trovare un canale e fai clic su di esso per avviarlo.

3. CARICAMENTO DELLA GUIDA TV (EPG)
--------------------------------------------------
- Nel secondo campo in alto, inserisci l'URL di una guida XMLTV (.xml o .xml.gz).
- Per caricare un file EPG dal PC: clicca su "File EPG".
- Clicca su "Carica EPG".
- Nella colonna di destra comparira' il programma IN ONDA ORA e la programmazione successiva.

4. RISOLUZIONE RAPIDA PROBLEMI & VLC
--------------------------------------------------
- Il canale non si apre nel browser:
  1. Assicurati che sia spuntata la casella "Usa Proxy Anti-CORS" in alto a destra.
  2. Se il browser continua a non riprodurre il flusso, clicca su "▶ Apri su VLC" in alto a destra.
- Avvio rapido su VLC dalla finestra desktop:
  Incolla un URL .m3u8 nel campo di testo della finestra principale e clicca su "▶ Riproduci subito su VLC Media Player".

5. COMPILAZIONE IN FILE .EXE
--------------------------------------------------
- Apri il terminale nella cartella dello script ed esegui:
  pyinstaller --noconsole --onefile --name "IPTV_Suite" iptv_suite_all_in_one.py
- Troverai il file pronto nella cartella: dist\IPTV_Suite.exe
