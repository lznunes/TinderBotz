'''
Created by Frederikme (TeetiFM)

This script is meant to be user friendly for beginning users.
Definitly take a look at quickstart.py for more features!
'''

from tinderbotz.session import Session
from selenium.common.exceptions import InvalidSessionIdException, NoSuchWindowException

if __name__ == "__main__":

    session = None
    try:
        # creates instance of session
        session = Session()
        print("Para cancelar a qualquer momento, pressione Ctrl+C neste terminal.")
    
        session.login_manually()
        answer = input("Login concluido. Iniciar ate 200 likes? Digite s para iniciar: ")
        if answer.strip().lower() == "s":
            session.like(amount=200, ratio="100%", sleep=1)

    except (KeyboardInterrupt, EOFError):
        print("\nExecucao cancelada pelo usuario.")
    except (InvalidSessionIdException, NoSuchWindowException):
        print("\nNavegador fechado. Execucao encerrada.")
    finally:
        if session is not None:
            session.close()
