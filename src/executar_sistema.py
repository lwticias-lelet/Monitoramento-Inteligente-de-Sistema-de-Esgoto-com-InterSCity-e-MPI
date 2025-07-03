"""
Script Principal para Execução do Sistema Completo
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import subprocess
import time
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from config.config import *

class GerenciadorSistema:
    """Gerenciador principal do sistema de monitoramento"""
    
    def __init__(self):
        self.processos = {}
        self.executando = True
        self.projeto_dir = BASE_DIR
        self.src_dir = SRC_DIR
        
        # Estado do sistema
        self.componentes = {
            'intersCity': {'status': 'PARADO', 'processo': None},
            'mpi': {'status': 'PARADO', 'processo': None},
            'gerador': {'status': 'PARADO', 'processo': None}
        }
    
    def log(self, message, nivel="INFO"):
        """Log com timestamp e nível"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {nivel}: {message}")
    
    def verificar_prerequisitos(self):
        """Verifica se todos os pré-requisitos estão atendidos"""
        self.log("🔍 Verificando pré-requisitos...")
        
        # Verificar arquivos Python
        arquivos_necessarios = [
            'sistema_monitoramento.py',
            'servidor_intersCity.py',
            'gerador_dados.py'
        ]
        
        for arquivo in arquivos_necessarios:
            caminho = self.src_dir / arquivo
            if caminho.exists():
                self.log(f"✅ {arquivo}")
            else:
                self.log(f"❌ {arquivo} não encontrado", "ERROR")
                return False
        
        # Verificar MPI
        try:
            result = subprocess.run(['mpiexec', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.log("✅ MPI disponível")
            else:
                self.log("❌ MPI não está funcionando", "ERROR")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log("❌ MPI não instalado ou não encontrado", "ERROR")
            return False
        
        # Verificar Python e bibliotecas
        try:
            import mpi4py, numpy, pandas, flask
            self.log("✅ Bibliotecas Python disponíveis")
        except ImportError as e:
            self.log(f"❌ Biblioteca não encontrada: {e}", "ERROR")
            return False
        
        # Verificar/criar diretórios
        setup_directories()
        self.log("✅ Diretórios configurados")
        
        return True
    
    def iniciar_intersCity(self):
        """Inicia o servidor InterSCity"""
        self.log("🌐 Iniciando servidor InterSCity...")
        
        try:
            cmd = [sys.executable, str(self.src_dir / 'servidor_intersCity.py')]
            processo = subprocess.Popen(
                cmd,
                cwd=str(self.projeto_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.componentes['intersCity']['processo'] = processo
            self.componentes['intersCity']['status'] = 'RODANDO'
            
            self.log("✅ Servidor InterSCity iniciado")
            
            # Aguardar servidor inicializar
            time.sleep(3)
            
            # Tentar abrir dashboard
            try:
                url = f"http://localhost:{INTERSITY_CONFIG['port']}"
                webbrowser.open(url)
                self.log(f"🌍 Dashboard aberto: {url}")
            except Exception:
                self.log(f"📊 Dashboard disponível: http://localhost:{INTERSITY_CONFIG['port']}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao iniciar InterSCity: {e}", "ERROR")
            self.componentes['intersCity']['status'] = 'ERRO'
            return False
    
    def iniciar_sistema_mpi(self):
        """Inicia o sistema MPI"""
        self.log("🚀 Iniciando sistema MPI...")
        
        try:
            num_processos = SISTEMA_CONFIG['mpi_processes']
            cmd = [
                'mpiexec', '-n', str(num_processos), 
                'python', str(self.src_dir / 'sistema_monitoramento.py')
            ]
            
            processo = subprocess.Popen(
                cmd,
                cwd=str(self.projeto_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.componentes['mpi']['processo'] = processo
            self.componentes['mpi']['status'] = 'RODANDO'
            
            self.log(f"✅ Sistema MPI iniciado com {num_processos} processos")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao iniciar sistema MPI: {e}", "ERROR")
            self.componentes['mpi']['status'] = 'ERRO'
            return False
    
    def iniciar_gerador_dados(self):
        """Inicia gerador de dados se necessário"""
        # Verificar se já existem dados
        if DADOS_ANYLOGIC.exists() and DADOS_ANYLOGIC.stat().st_size > 100:
            self.log("📊 Dados do AnyLogic já existem, não iniciando gerador")
            return True
        
        self.log("📈 Iniciando gerador de dados...")
        
        try:
            cmd = [sys.executable, str(self.src_dir / 'gerador_dados.py')]
            processo = subprocess.Popen(
                cmd,
                cwd=str(self.projeto_dir),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Enviar opção para gerar dados contínuos
            processo.stdin.write("2\n")
            processo.stdin.flush()
            
            self.componentes['gerador']['processo'] = processo
            self.componentes['gerador']['status'] = 'RODANDO'
            
            self.log("✅ Gerador de dados iniciado")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao iniciar gerador: {e}", "ERROR")
            self.componentes['gerador']['status'] = 'ERRO'
            return False
    
    def monitorar_componentes(self):
        """Monitora status dos componentes"""
        while self.executando:
            try:
                for nome, info in self.componentes.items():
                    processo = info['processo']
                    if processo and processo.poll() is not None:
                        # Processo finalizou
                        stdout, stderr = processo.communicate()
                        
                        if stderr and len(stderr.strip()) > 0:
                            self.log(f"⚠️ {nome} finalizou com erro: {stderr[:200]}...", "WARNING")
                        else:
                            self.log(f"ℹ️ {nome} finalizou normalmente")
                        
                        info['status'] = 'PARADO'
                        info['processo'] = None
                
                time.sleep(10)  # Verificar a cada 10 segundos
                
            except Exception as e:
                self.log(f"Erro no monitor: {e}", "ERROR")
                time.sleep(30)
    
    def mostrar_status_periodico(self):
        """Mostra status do sistema periodicamente"""
        while self.executando:
            try:
                self.log("📊 STATUS DO SISTEMA:")
                
                for nome, info in self.componentes.items():
                    status = info['status']
                    emoji = "✅" if status == "RODANDO" else "❌" if status == "ERRO" else "⏸️"
                    self.log(f"   {emoji} {nome.title()}: {status}")
                
                # Verificar dados
                if DADOS_ANYLOGIC.exists():
                    tamanho = DADOS_ANYLOGIC.stat().st_size
                    self.log(f"   📊 Dados AnyLogic: {tamanho} bytes")
                else:
                    self.log("   📊 Dados AnyLogic: Não encontrados")
                
                # Verificar logs
                logs_dir = LOGS_DIR
                if logs_dir.exists():
                    arquivos_log = list(logs_dir.glob("*.log"))
                    self.log(f"   📝 Logs: {len(arquivos_log)} arquivos")
                
                self.log(f"   🌍 Dashboard: http://localhost:{INTERSITY_CONFIG['port']}")
                self.log("-" * 50)
                
                time.sleep(60)  # Status a cada 1 minuto
                
            except Exception as e:
                self.log(f"Erro no status: {e}", "ERROR")
                time.sleep(60)
    
    def finalizar_sistema(self):
        """Finaliza todos os componentes"""
        self.log("🛑 Finalizando sistema...")
        self.executando = False
        
        for nome, info in self.componentes.items():
            processo = info['processo']
            if processo and processo.poll() is None:
                try:
                    self.log(f"🔄 Finalizando {nome}...")
                    processo.terminate()
                    
                    # Aguardar finalização
                    try:
                        processo.wait(timeout=10)
                        self.log(f"✅ {nome} finalizado")
                    except subprocess.TimeoutExpired:
                        self.log(f"⚠️ Forçando finalização de {nome}...")
                        processo.kill()
                        
                except Exception as e:
                    self.log(f"❌ Erro ao finalizar {nome}: {e}", "ERROR")
                
                info['status'] = 'PARADO'
                info['processo'] = None
        
        self.log("🏁 Sistema completamente finalizado")
    
    def executar_sistema_completo(self):
        """Executa o sistema completo"""
        print("=" * 70)
        print("🏗️  SISTEMA DE MONITORAMENTO DE ESGOTO URBANO")
        print("   Integração: AnyLogic + MPI + InterSCity")
        print("   Ambiente: VS Code + PowerShell")
        print("=" * 70)
        
        try:
            # 1. Verificar pré-requisitos
            if not self.verificar_prerequisitos():
                self.log("❌ Pré-requisitos não atendidos", "ERROR")
                return False
            
            # 2. Iniciar componentes em ordem
            if not self.iniciar_intersCity():
                self.log("❌ Falha ao iniciar InterSCity", "ERROR")
                return False
            
            time.sleep(3)
            
            # 3. Verificar se precisa de gerador de dados
            self.iniciar_gerador_dados()
            
            time.sleep(5)
            
            # 4. Iniciar sistema MPI
            if not self.iniciar_sistema_mpi():
                self.log("❌ Falha ao iniciar sistema MPI", "ERROR")
                self.finalizar_sistema()
                return False
            
            # 5. Iniciar threads de monitoramento
            monitor_thread = threading.Thread(target=self.monitorar_componentes, daemon=True)
            status_thread = threading.Thread(target=self.mostrar_status_periodico, daemon=True)
            
            monitor_thread.start()
            status_thread.start()
            
            # 6. Instruções finais
            print("\n" + "=" * 70)
            print("🚀 SISTEMA INICIADO COM SUCESSO!")
            print("=" * 70)
            print(f"📊 Dashboard InterSCity: http://localhost:{INTERSITY_CONFIG['port']}")
            print(f"🔍 Logs do sistema: {LOGS_DIR}")
            print(f"📁 Dados salvos: {DATA_DIR}")
            print("⚠️  IMPORTANTE: Sistema gerando dados automaticamente")
            print("⏹️  Para parar: Pressione Ctrl+C")
            print("📋 Status mostrado a cada minuto")
            print("=" * 70)
            
            # 7. Loop principal
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.log("👤 Interrupção solicitada pelo usuário")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Erro crítico: {e}", "ERROR")
            return False
        
        finally:
            self.finalizar_sistema()

def modo_menu():
    """Modo interativo com menu"""
    gerenciador = GerenciadorSistema()
    
    while True:
        print("\n" + "=" * 60)
        print("🏗️  SISTEMA DE MONITORAMENTO - MENU PRINCIPAL")
        print("=" * 60)
        print("1. 🚀 Executar sistema completo")
        print("2. 🌐 Iniciar apenas InterSCity")
        print("3. 📊 Gerar dados de teste")
        print("4. 🔍 Verificar pré-requisitos")
        print("5. 📋 Verificar status dos componentes")
        print("6. ❌ Sair")
        print("=" * 60)
        
        try:
            opcao = input("📝 Escolha uma opção (1-6): ").strip()
            
            if opcao == '1':
                print("\n🚀 Iniciando sistema completo...")
                gerenciador.executar_sistema_completo()
                
            elif opcao == '2':
                print("\n🌐 Iniciando apenas InterSCity...")
                if gerenciador.iniciar_intersCity():
                    print("✅ InterSCity rodando. Pressione Ctrl+C para parar.")
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        gerenciador.finalizar_sistema()
                
            elif opcao == '3':
                print("\n📊 Iniciando gerador de dados...")
                from gerador_dados import menu_interativo
                menu_interativo()
                
            elif opcao == '4':
                print("\n🔍 Verificando pré-requisitos...")
                if gerenciador.verificar_prerequisitos():
                    print("✅ Todos os pré-requisitos atendidos!")
                else:
                    print("❌ Alguns pré-requisitos não atendidos.")
                
            elif opcao == '5':
                print("\n📋 Status dos componentes:")
                for nome, info in gerenciador.componentes.items():
                    print(f"   {nome.title()}: {info['status']}")
                
            elif opcao == '6':
                print("👋 Saindo...")
                break
                
            else:
                print("❌ Opção inválida! Digite um número de 1 a 6.")
                
        except KeyboardInterrupt:
            print("\n👋 Saindo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--completo":
        # Modo execução direta
        gerenciador = GerenciadorSistema()
        gerenciador.executar_sistema_completo()
    else:
        # Modo menu
        modo_menu()

if __name__ == "__main__":
    main()