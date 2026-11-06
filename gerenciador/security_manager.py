import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

class SecurityManager:
    DB_PATH = "deven_wealth.db"
    ENC_PATH = "deven_wealth.db.enc"

    @staticmethod
    def _derivar_chave(senha: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(senha.encode()))

    @staticmethod
    def validar_senha(senha: str) -> tuple[bool, str]:
        if len(senha) < 8:
            return False, "A senha deve ter no mínimo 8 caracteres."
        
        caracteres_especiais = ['!', ';', '@', '#', '$', '%', '&', '*', '_', '-']
        if not any(char in senha for char in caracteres_especiais):
            return False, f"A senha deve conter ao menos um caractere especial: {' '.join(caracteres_especiais)}"
            
        return True, "Senha válida"

    @staticmethod
    def banco_esta_criptografado() -> bool:
        return os.path.exists(SecurityManager.ENC_PATH)

    @staticmethod
    def banco_aberto() -> bool:
        return os.path.exists(SecurityManager.DB_PATH)

    @staticmethod
    def criar_banco_seguro(senha: str):
        # Cria um arquivo vazio e o criptografa
        if not os.path.exists(SecurityManager.DB_PATH):
            open(SecurityManager.DB_PATH, 'w').close()
            SecurityManager.criptografar_banco(senha)

    @staticmethod
    def criptografar_banco(senha: str):
        if not os.path.exists(SecurityManager.DB_PATH):
            return
            
        with open(SecurityManager.DB_PATH, 'rb') as f:
            dados = f.read()
            
        salt = os.urandom(16)
        chave = SecurityManager._derivar_chave(senha, salt)
        f_fernet = Fernet(chave)
        dados_criptografados = f_fernet.encrypt(dados)
        
        with open(SecurityManager.ENC_PATH, 'wb') as f_enc:
            f_enc.write(salt + dados_criptografados)
            
        # Apaga o banco original não criptografado
        os.remove(SecurityManager.DB_PATH)

    @staticmethod
    def descriptografar_banco(senha: str) -> bool:
        if not os.path.exists(SecurityManager.ENC_PATH):
            return False
            
        with open(SecurityManager.ENC_PATH, 'rb') as f_enc:
            conteudo = f_enc.read()
            
        salt = conteudo[:16]
        dados_criptografados = conteudo[16:]
        
        chave = SecurityManager._derivar_chave(senha, salt)
        f_fernet = Fernet(chave)
        
        try:
            dados_descriptografados = f_fernet.decrypt(dados_criptografados)
            with open(SecurityManager.DB_PATH, 'wb') as f_db:
                f_db.write(dados_descriptografados)
            return True
        except InvalidToken:
            return False

    @staticmethod
    def trancar_cofre(senha: str):
        if SecurityManager.banco_aberto():
            SecurityManager.criptografar_banco(senha)
