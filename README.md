# Ia-Asserv_Com

Un bout de code en python pour gérer la com' entre l'IA (sur une rasp) et l'asserv (un STM32).
La com' se fait en utilisant le protocol cbor (sorte de json au format binaire), protégé par un CRC32.

## Environnement 

On utilise un virtual env python pour récuperer les dépendances, pour automatiser cela, il suffit de sourcer l'environnement :

```
source env.bash 
```