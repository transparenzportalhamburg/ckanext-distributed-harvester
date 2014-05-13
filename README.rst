============================================================================================
ckanext-distributedharvest - CKAN-Erweiterung zur verteilten Ausfuehrung von Harvest-Jobs
============================================================================================


Diese Erweiterung ergaenzt das CKAN-Plugin ckanext-harvest um die Funktionen
zur parallelen Ausfuehrung von Harvest-Jobs.

Installation
============

1. Die Erweiterung ist aktuell nur mit der Message Broker Software RabbitMQ
   kompatibel:

   * `RabbitMQ <http://www.rabbitmq.com/>`_: To install it, run::

      sudo apt-get install rabbitmq-server


2. Installation des Plugins in der virtuellen Python-Umgebung:

   *Wichtig:* Dises Plugin basiert auf der aktuellen Version der CKAN-Erweiterung ckanext-harvest v2.0.
       
     Installation von ckanext-harvest::
   
        (pyenv) $ pip install -e git+https://race.informatik.uni-hamburg.de/inforeggroup/ckanext-distributed-harvester.git#egg=ckanext-distributed-harvester

     Installation der restlichen Python-Module, die fuer das Plugin erforderlich sind::
   
        (pyenv) $ pip install -r pip-requirements.txt
   
     Installation von ckanext-distributed-harvest ueber ein pip-Kommando::
     
       (pyenv) $ pip install -e git+https://github.com/okfn/ckanext-harvest.git@release-v2.0#egg=ckanext-harvest
     
     Installation von ckanext-distributed-harvest ueber python-Befehle::
     
       (pyenv) $ git clone git@race.informatik.uni-hamburg.de:inforeggroup/ckanext-distributed-harvester.git
       (pyenv) $ cd ckanext-distributed-harvester
       (pyenv) $ python setup.py develop
       (pyenv) $ python setup.py install
     
   *Wichtig:* Es sind keine weiteren Python-Module fuer die Ausfuehrung dieses Plugins noetig.
       
3. Folgende Plugins muessen in der Konfigurationsdatei (development.ini) angegeben werden, um diese zu aktivieren::

      ckan.plugins = harvest distributed_harvest

4. Ausserdem muss die Message Broker Software auf RabbitMQ gesetzt werden::

    ckan.harvest.mq.type = ampq




Kommandozeilenbefehle
=====================

Die folgenden Befehle koennen von der Kommandozeile unter vorhergehenden Angabe von 
`paster --plugin=ckanext-distributedharvest distributed-harvester` ausgefuehrt werden::

      1. run_distributed_harvester {source-id} {harvester-titel} | {source-id} {gather-routing-key} {fetch-routing-key}
        - startet parallele Harvester-Jobs mit generierten Namen (aus harvester-titel) oder mit uebergebenen Bezeichnern
        - bis auf exchange-name sind alle Parameter Pflichtangaben


      2. distributed_gather_consumer {harvester-titel} | {gather-queue-name} {gather-routing-key} {exchange-name}
        - startet parallele Gather-Konsumenten mit generierten Namen (aus harvester-titel) oder mit uebergebenen Bezeichnern
        - bis auf exchange-name sind alle Parameter Pflichtangaben
          
          
      3. distributed_fetch_consumer {harvester-titel} | {fetch-queue-name} {fetch-routing-key} {exchange-name}
        - startet parallele Fetch-Konsumenten mit generierten Namen (aus harvester-titel) oder mit uebergebenen Bezeichnern
        - bis auf exchange-name sind alle Parameter Pflichtangaben
         

      4. purge_queues {harvester-titel} | {gather-queue-name} {fetch-queue-name}
        - entfernt alle Jobs und Harvest-Objekte von der Gather-Queue und der Fetch-Queue
        - falls harvester-titel gegeben ist, werden die Namen fuer die erforderlichen Queues daraus gebildet oder sie
          koennen direkt uebergeben werden
        
        
     Diese Kommandos koennen direkt vom Verzeichnis `ckanext-distributedharvest` 
     ausgefuehrt werden.
     
      paster --plugin=ckanext-distributedharvest distributed-harvester run_distributed_harvester #1234 test-titel --config=../ckan/development.ini




Authorization
=============

Das Plugin ckanext-distributedharvest setzt dieselben Zugriffabfragen 
wie ckanext-harvest ein.



Harvester-Jobs ausfuehren
=========================

Die Harvester-Erweiterung setzt wie ckanext-harvest auch weiterhin zwei Queues ein, um die 
Nachrichten zwischen den Harvester-Porzessen zu verwalten.

Zu Beginn sollte der Gather-Konsument mit einem beliebigen Namen fuer die Verwaltung der Queues gestartet werden. 
Dabei sollte dieser Name auch dem Fetch-Konsumenten sowie dem Run-Kommando uebergeben werden, da im Run-Befehl aus
dieser Bezeichnung die Namen der Routing-Schluessel aus den beiden anderen Befehlen erzeugt wird::

      paster --plugin=ckanext-distributedharvest distributed-harvester distributed_gather_consumer harvesterTest --config=development.ini

In einer weiteren Konsole den Fetch-Konsumenten starten::

      paster --plugin=ckanext-distributedharvest distributed-harvester distributed_fetch_consumer harvesterTest --config=development.ini

In einer weiteren Konsole den Run-Befehl ausfuehren::

      paster --plugin=ckanext-distributedharvest distributed-harvester run_distributed_harvester sourcetest harvesterTest --config=development.ini

Fuer alle anderen Harvester muessen diese Kommandos (mit neuem Namen fuer ``harvesterTest``) 
in neunen Konsolen ausgefuehrt werden, damit diese verteilt verarbeitet werden koennen.



Ueber dieselben Kommandos lassen sich auch die jeweiligen Konsumenten mit individuellen 
Namen für die einzelnen Queues, Routing-Keys und Exchanges definieren::
      paster --plugin=ckanext-distributedharvest distributed-harvester distributed_gather_consumer gather_queue_harvesterTest gather_routing_key_harvesterTest --config=development.ini
      paster --plugin=ckanext-distributedharvest distributed-harvester distributed_fetch_consumer fetch_queue_harvesterTest fetch_routing_key_harvesterTest --config=development.ini
      paster --plugin=ckanext-distributedharvest distributed-harvester run_distributed_harvester sourcetest gather_routing_key_harvesterTest fetch_routing_key_harvesterTest --config=development.ini
  

Falls der Bedarf besteht, zwei oder mehrere Harvester sequentuiell ueber eine Queue 
zu verarbeiten, dann sollten zunaechst alle Prozesse wie oben beschrieben
gestartet und anschliessend jeder weitere sequentiell zu verarbeitende Harvester  
durch ein Run-Kommando mit demselben Bezeichner ausgefuehrt werden::

      paster --plugin=ckanext-distributedharvest distributed-harvester run_distributed_harvester sourcetest2 harvesterTest --config=development.ini
      paster --plugin=ckanext-distributedharvest distributed-harvester run_distributed_harvester sourcetest3 harvesterTest --config=development.ini
      ...