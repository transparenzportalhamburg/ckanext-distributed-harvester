English Version:

====================================================================================
ckanext-distributed-harvester - A ckan extension to execute distributed Harvest jobs
====================================================================================
|
This extension extends the CKAN plugin ckanext-harvest to support distributed harvesting capabilities.

|
|

Plugin Installation
===================
|
1. The extension is currently only compatible with the Message Broker Software RabbitMQ:

   * `RabbitMQ <http://www.rabbitmq.com/>`_: To install it, run::

      sudo apt-get install rabbitmq-server

2. Install the extension into your python environment:

   *Note:* This plugin is based on the current version of CKAN extension ckanext-harvest v2.0.
       
     To install it, run::
   
        (pyenv) $ pip install -e git+https://race.informatik.uni-hamburg.de/inforeggroup/ckanext-distributed-harvester.git#egg=ckanext-distributed-harvester
       
     Install the rest of python modules required by the extension::
   
        (pyenv) $ pip install -r pip-requirements.txt
|      
3. Your CKAN configuration ini file should contain the following plugins::

      ckan.plugins = harvest distributed_harvest

4. Define RabbitMQ as your backend::

    ckan.harvest.mq.type = ampq
|
|

Commands
========
|
The following operations can be run from the command line using the 
`paster --plugin=ckanext-distributedharvest distributed-harvester` command::

      1. run_distributed_harvester {source-id} {harvest-title} | {source-id} {gather-routing-key} {fetch-routing-key}
        - starts parallel harvest jobs with with generated name (from harvest-title) or with the given keys


      2. distributed_gather_consumer {harvest-title} | {gather-queue-name} {gather-routing-key} {exchange-name}
        - starts parallel gather consumer with generated name (from harvest-title) or with the given keys and exchange-name
        - all fields are mandatory except from exchange-name
          
          
      3. distributed_fetch_consumer {harvest-title} | {fetch-queue-name} {fetch-routing-key} {exchange-name}
        - starts parallel fetch consumer with generated name (from harvest-title) or with the given keys and exchange-name
        - all fields are mandatory except from exchange-name
         

      4. purge_queues {harvest-title} | {gather-queue-name} {fetch-queue-name}
        - deletes all harvest jobs und harvest objects from the gather queue and the fetch queue

        
      The commands should be run with activated Python virtual environment and refer to your sites configuration file, e.g.:
     
      paster --plugin=ckanext-distributed-harvest distributed-harvester run_distributed_harvester #1234 test-title --config=../ckan/development.ini
|
|

Authorization
=============
|
The plugin ckanext-distributed-harvest uses the same access control mechanisms as ckanext-harvest.

|

Run Harvest Jobs
================
|
The Harvester extension uses two queues in order to manage messages between the harvest processes.

Run the following command to start the gather consumer. The parameter ``harvesterTest`` specifies a name 
which will be used to manage the queues belonging to a harvest source (e.g. for creating routing keys). 
Thus, the fetch consumer and the run command of the same harvest source should also started with the same name.::

      paster --plugin=ckanext-distributed-harvest distributed-harvester distributed_gather_consumer harvesterTest --config=development.ini

On another console, run the following command to start the fetch consumer::

      paster --plugin=ckanext-distributed-harvest distributed-harvester distributed_fetch_consumer harvesterTest --config=development.ini

Finally, on a third console, run the following command to start a harvesting job assigned to the source ``harvesterTest``::

      paster --plugin=ckanext-distributed-harvest distributed-harvester run_distributed_harvester sourcetest harvesterTest --config=development.ini

For all other harvest sources, you will need to run these commands (with a new name for ``harvesterTest``) 
in other consoles in order to execute harvesting jobs in parallel processes.

|

All necessary routing keys, queues and exchanges will be generated during the execution of the harvesting jobs. However, you
are free to run these commands with other parameters and define your own names for them::

      paster --plugin=ckanext-distributed-harvest distributed-harvester distributed_gather_consumer gather_queue_harvesterTest gather_routing_key_harvesterTest exchange-name --config=development.ini
      paster --plugin=ckanext-distributed-harvest distributed-harvester distributed_fetch_consumer fetch_queue_harvesterTest fetch_routing_key_harvesterTest exchange-name --config=development.ini
      paster --plugin=ckanext-distributed-harvest distributed-harvester run_distributed_harvester sourcetest gather_routing_key_harvesterTest fetch_routing_key_harvesterTest exchange-name --config=development.ini
  

If you use for various harvest sources the same queue names and routing keys, the harvesting jobs will be 
processed sequentially::

      paster --plugin=ckanext-distributed-harvest distributed-harvester run_distributed_harvester sourcetest2 harvesterTest --config=development.ini
      paster --plugin=ckanext-distributed-harvest distributed-harvester run_distributed_harvester sourcetest3 harvesterTest --config=development.ini
      ...
|
|     
      
License
=======
|
|

German Version:

==========================================================================================
ckanext-distributed-harvest - CKAN-Erweiterung zur verteilten Ausfuehrung von Harvest-Jobs
==========================================================================================
|
Diese Erweiterung erweitert das CKAN-Plugin ckanext-harvest um die Funktionen
zur parallelen Ausfuehrung von Harvest-Jobs.

|
|

Installation
============
|
1. Die Erweiterung ist aktuell nur mit der Message Broker Software RabbitMQ
   kompatibel:

   * `RabbitMQ <http://www.rabbitmq.com/>`_: Fuer die Installation::

      sudo apt-get install rabbitmq-server

2. Installation des Plugins in der virtuellen Python-Umgebung:

   *Wichtig:* Dieses Plugin basiert auf der aktuellen Version der CKAN-Erweiterung ckanext-harvest v2.0.
       
     Installation von ckanext-harvest::
   
        (pyenv) $ pip install -e git+https://race.informatik.uni-hamburg.de/inforeggroup/ckanext-distributed-harvester.git#egg=ckanext-distributed-harvester

     Installation der restlichen Python-Module, die fuer das Plugin erforderlich sind::
   
        (pyenv) $ pip install -r pip-requirements.txt
       
3. Folgende Plugins muessen in der Konfigurationsdatei (development.ini) angegeben werden, um diese zu aktivieren::

      ckan.plugins = harvest distributed_harvest

4. Ausserdem muss die Message Broker Software auf RabbitMQ gesetzt werden::

    ckan.harvest.mq.type = ampq
|
|

Kommandozeilenbefehle
=====================
|
Die folgenden Befehle koennen von der Kommandozeile unter vorhergehenden Angabe von 
`paster --plugin=ckanext-distributedharvest distributed-harvester` ausgefuehrt werden::

      1. run_distributed_harvester {source-id} {harvester-titel} | {source-id} {gather-routing-key} {fetch-routing-key}
        - startet parallele Harvester-Jobs mit generierten Namen (aus harvester-titel) oder mit uebergebenen Bezeichnern

      2. distributed_gather_consumer {harvester-titel} | {gather-queue-name} {gather-routing-key} {exchange-name}
        - startet parallele Gather-Konsumenten mit generierten Namen (aus harvester-titel) oder mit uebergebenen Bezeichnern
        - bis auf exchange-name sind alle Parameter Pflichtangaben
          
          
      3. distributed_fetch_consumer {harvester-titel} | {fetch-queue-name} {fetch-routing-key} {exchange-name}
        - startet parallele Fetch-Konsumenten mit generierten Namen (aus harvester-titel) oder mit uebergebenen Bezeichnern
        - bis auf exchange-name sind alle Parameter Pflichtangaben
         

      4. purge_queues {harvester-titel} | {gather-queue-name} {fetch-queue-name}
        - entfernt alle Jobs und Harvest-Objekte von der Gather-Queue und der Fetch-Queue

        
     Diese Kommandos koennen direkt vom Verzeichnis `ckanext-distributedharvest` 
     ausgefuehrt werden.
     
      paster --plugin=ckanext-distributedharvest distributed-harvester run_distributed_harvester #1234 test-titel --config=../ckan/development.ini
|
|

Authorization
=============
|
Das Plugin ckanext-distributedharvest setzt dieselben Zugriffsabfragen 
wie ckanext-harvest ein.

|

Harvester-Jobs ausfuehren
=========================
|
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

|

Ueber dieselben Kommandos lassen sich auch die jeweiligen Konsumenten mit individuellen 
Namen für die einzelnen Queues, Routing-Keys und Exchanges definieren::
      paster --plugin=ckanext-distributedharvest distributed-harvester distributed_gather_consumer gather_queue_harvesterTest gather_routing_key_harvesterTest exchange-name --config=development.ini
      paster --plugin=ckanext-distributedharvest distributed-harvester distributed_fetch_consumer fetch_queue_harvesterTest fetch_routing_key_harvesterTest exchange-name --config=development.ini
      paster --plugin=ckanext-distributedharvest distributed-harvester run_distributed_harvester sourcetest gather_routing_key_harvesterTest fetch_routing_key_harvesterTest exchange-name --config=development.ini
  

Falls der Bedarf besteht, zwei oder mehrere Harvester sequentuiell ueber eine Queue 
zu verarbeiten, dann sollten zunaechst alle Prozesse wie oben beschrieben
gestartet und anschliessend jeder weitere sequentiell zu verarbeitende Harvester  
durch ein Run-Kommando mit demselben Bezeichner ausgefuehrt werden::

      paster --plugin=ckanext-distributedharvest distributed-harvester run_distributed_harvester sourcetest2 harvesterTest --config=development.ini
      paster --plugin=ckanext-distributedharvest distributed-harvester run_distributed_harvester sourcetest3 harvesterTest --config=development.ini
      ...
|
|
      
Lizenz
======
|