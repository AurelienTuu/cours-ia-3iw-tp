"""Point d'entree du serveur, voie Python. FOURNI : ne le modifiez pas.

Il assemble les routes des trois seances et sert le front. Votre travail est
dans les fichiers de seance :

    s09_resumer.py      seance 9   TODO 1 a 5
    s10_assistant.py    seance 10  TODO 6 a 8
    s13_index.py        seance 13  TODO 9 a 11
    s13_documents.py    seance 13  TODO 12

Lancement, depuis la racine du depot :
    make app
"""
import s09_resumer
import s10_assistant
import s13_documents
from fourni.transport import creer_application, servir_le_front

app = creer_application()

app.include_router(s09_resumer.routeur)
app.include_router(s10_assistant.routeur)
app.include_router(s13_documents.routeur)

# Toujours en dernier : la racine sert le front et attrape le reste.
servir_le_front(app)
