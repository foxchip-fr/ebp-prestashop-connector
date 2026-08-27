"""
MIT License

Copyright (c) 2024 Foxchip

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import tempfile
from pathlib import Path

from psebpconnector.connector import Connector

try:                                  # Windows (cible de production)
    import msvcrt
    fcntl = None
except ImportError:                   # Linux/CI
    msvcrt = None
    import fcntl


def _acquire_single_instance_lock(lock_file):
    """ Verrou pose par l'OS : il est relache automatiquement si le process meurt (contrairement a
        un simple fichier temoin, qui bloquerait definitivement la facturation apres un crash).
        Retourne True si le verrou est obtenu, False si une autre instance tourne deja. """
    try:
        if msvcrt is not None:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _release_single_instance_lock(lock_file):
    try:
        if msvcrt is not None:
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def main():
    if len(sys.argv) < 2:
        config_file_path = Path(os.environ['PROGRAMDATA']) / Path('PS EBP Connector') / Path('config.ini')
    else:
        config_file_path = sys.argv[1]

    # Verrou mono-instance : deux runs simultanes (run horaire qui deborde, lancement manuel)
    # exporteraient les MEMES commandes (elles ne sont marquees exportees qu'a la fin) et EBP
    # creerait deux fois chaque facture.
    lock_path = Path(tempfile.gettempdir()) / 'ps_ebp_connector.lock'
    lock_file = open(lock_path, 'a+')
    if not _acquire_single_instance_lock(lock_file):
        lock_file.close()
        print("ps_ebp_connector : une autre instance est deja en cours, run ignore.", file=sys.stderr)
        return 1

    try:
        # Le code retour doit remonter a la tache planifiee, sinon un run en echec est rapporte
        # comme un succes et personne ne le voit.
        return Connector(Path(config_file_path)).run()
    finally:
        _release_single_instance_lock(lock_file)
        lock_file.close()


if __name__ == '__main__':
    sys.exit(main())
