# -*- coding: gbk -*-
# copy from cnblogs
import os
import subprocess
import signal
import pwd
import sys
 
class MockLogger(object):
    '''ģ����־�ࡣ���㵥Ԫ���ԡ�'''
    def __init__(self):
        self.info = self.error = self.critical = self.debug
 
    def debug(self, msg):
        print "LOGGER:"+msg
 
class Shell(object):
    '''���Shell�ű��İ�װ��
    ִ�н�������Shell.ret_code, Shell.ret_info, Shell.err_info��
    run()Ϊ��ͨ���ã���ȴ�shell����ء�
    run_background()Ϊ�첽���ã������̷��أ����ȴ�shell�������
    �첽����ʱ������ʹ��get_status()��ѯ״̬����ʹ��wait()��������״̬��
    �ȴ�shellִ����ɡ�
    �첽����ʱ��ʹ��kill()ǿ��ֹͣ�ű�����Ȼ��Ҫʹ��wait()�ȴ������˳���
    TODO δ��֤Shell����г��������ʱ�������
    '''
    def __init__(self, cmd):
        self.cmd = cmd  # cmd��������Ͳ���
        self.ret_code = None
        self.ret_info = None
        self.err_info = None
        #ʹ��ʱ���滻Ϊ�����logger
        self.logger = MockLogger()
         
    def run_background(self):
        '''�Է�������ʽִ��shell���Popen��Ĭ�Ϸ�ʽ����
        '''
        self.logger.debug("run %s"%self.cmd)
        # Popen��Ҫִ�е��������ʱ���׳�OSError�쳣����shell=True��
        # shell�ᴦ��������ڵĴ������û����OSError�쳣���ʲ��ô���
        self._process = subprocess.Popen(self.cmd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) #������
         
    def run(self):
        '''��������ʽִ��shell���
        '''
        self.run_background()
        self.wait()
         
    def run_cmd(self, cmd):
        '''ֱ��ִ��ĳ���������һ��ʵ���ظ�ʹ��ִ�ж������
        '''
        self.cmd = cmd
        self.run()
 
    def wait(self):
        '''�ȴ�shellִ����ɡ�
        '''
        self.logger.debug("waiting %s"%self.cmd)
        self.ret_info, self.err_info = self._process.communicate() #����
        # returncode: A negative value -N indicates that the child was
        # terminated by signal N
        self.ret_code = self._process.returncode
        self.logger.debug("waiting %s done. return code is %d"%(self.cmd,
                            self.ret_code))
 
    def get_status(self):
        '''��ȡ�ű�����״̬(RUNNING|FINISHED)
        '''
        retcode = self._process.poll()
        if retcode == None:
            status = "RUNNING"
        else:
            status = "FINISHED"
        self.logger.debug("%s status is %s"%(self.cmd, status))
        return status
 
    # Python2.4��subprocess��û��send_signal,terminate,kill
    # ��������Ҫɽկһ�ѣ�2.7��ֱ����self._process��kill()
    def send_signal(self, sig):
        self.logger.debug("send signal %s to %s"%(sig, self.cmd))
        os.kill(self._process.pid, sig)
 
    def terminate(self):
        self.send_signal(signal.SIGTERM)
 
    def kill(self):
        self.send_signal(signal.SIGKILL)
     
    def print_result(self):
        print "return code:", self.ret_code
        print "return info:", self.ret_info
        print " error info:", self.err_info
 
class RemoteShell(Shell):
    '''Զ��ִ�����ssh��ʽ����
    XXX �������ַ���������ܵ��µ���ʧЧ����˫���ţ���Ԫ��$
    NOTE ��cmd����˫���ţ���ʹ��RemoteShell2
    '''
    def __init__(self, cmd, ip):
        ssh = ("ssh -o PreferredAuthentications=publickey -o "
                "StrictHostKeyChecking=no -o ConnectTimeout=10")
        # ���ؼ��IP��Ч�ԣ�Ҳ���ؼ�����ι�ϵ��������shell�ᱨ��
        cmd = '%s %s "%s"'%(ssh, ip, cmd)
        Shell.__init__(self, cmd)
         
class RemoteShell2(RemoteShell):
    '''��RemoteShell��ͬ��ֻ�Ǳ任�����š�
    '''
    def __init__(self, cmd, ip):
        RemoteShell.__init__(self, cmd, ip)
        self.cmd = "%s %s '%s'"%(ssh, ip, cmd)
 
class SuShell(Shell):
    '''�л��û�ִ�����su��ʽ����
    XXX ֻ�ʺ�ʹ��root�л��������û���
        ��Ϊ�����л��û�����Ҫ�������룬����������ס��
    XXX �������ַ���������ܵ��µ���ʧЧ����˫���ţ���Ԫ��$
    NOTE ��cmd����˫���ţ���ʹ��SuShell2
    '''
    def __init__(self, cmd, user):
        if os.getuid() != 0: # ��root�û�ֱ�ӱ���
            raise Exception('SuShell must be called by root user!')
        cmd = 'su - %s -c "%s"'%(user, cmd)
        Shell.__init__(self, cmd)
 
class SuShell2(SuShell):
    '''��SuShell��ͬ��ֻ�Ǳ任�����š�
    '''
    def __init__(self, cmd, user):
        SuShell.__init__(self, cmd, user)
        self.cmd = "su - %s -c '%s'"%(user, cmd)
 
class SuShellDeprecated(Shell):
    '''�л��û�ִ�����setuid��ʽ����
    ִ�еĺ���Ϊrun2��������run
    XXX �ԡ����ɾ����ķ�ʽ���У����л��û����飬����������Ϣ���䡣
    XXX �޷���ȡ�����ret_code, ret_info, err_info
    XXX ֻ�ʺ�ʹ��root�л��������û���
    '''
    def __init__(self, cmd, user):
        self.user = user
        Shell.__init__(self, cmd)
 
    def run2(self):
        if os.getuid() != 0: # ��root�û�ֱ�ӱ���
            raise Exception('SuShell2 must be called by root user!')
        child_pid = os.fork()
        if child_pid == 0: # �ӽ��̸ɻ�
            uid, gid = pwd.getpwnam(self.user)[2:4]
            os.setgid(gid) # ������������
            os.setuid(uid)
            self.run()
            sys.exit(0) # �ӽ����˳�����ֹ����ִ����������
        else: # �����̵ȴ��ӽ����˳�
            os.waitpid(child_pid, 0)
         
if __name__ == "__main__":
    '''test code'''
    # 1. test normal
    sa = Shell('who')
    sa.run()
    sa.print_result()
     
    # 2. test stderr
    sb = Shell('ls /export/dir_should_not_exists')
    sb.run()
    sb.print_result()
     
    # 3. test background
    sc = Shell('sleep 1')
    sc.run_background()
    print 'hello from parent process'
    print "return code:", sc.ret_code
    print "status:", sc.get_status()
    sc.wait()
    sc.print_result()
     
    # 4. test kill
    import time
    sd = Shell('sleep 2')
    sd.run_background()
    time.sleep(1)
    sd.kill()
    sd.wait() # NOTE, still need to wait
    sd.print_result()
     
    # 5. test multiple command and uncompleted command output
    se = Shell('pwd;sleep 1;pwd;pwd')
    se.run_background()
    time.sleep(1)
    se.kill()
    se.wait() # NOTE, still need to wait
    se.print_result()
     
    # 6. test wrong command
    sf = Shell('aaaaa')
    sf.run()
    sf.print_result()
     
    # 7. test instance reuse to run other command
    sf.cmd = 'echo aaaaa'
    sf.run()
    sf.print_result()
     
    sg = RemoteShell('pwd', '127.0.0.1')
    sg.run()
    sg.print_result()
     
    # unreachable ip
    sg2 = RemoteShell('pwd', '17.0.0.1')
    sg2.run()
    sg2.print_result()
     
    # invalid ip
    sg3 = RemoteShell('pwd', '1711.0.0.1')
    sg3.run()
    sg3.print_result()
     
    # ip without trust relation
    sg3 = RemoteShell('pwd', '10.145.132.247')
    sg3.run()
    sg3.print_result()
     
     
    sh = SuShell('pwd', 'ossuser')
    sh.run()
    sh.print_result()
     
    # wrong user
    si = SuShell('pwd', 'ossuser123')
    si.run()
    si.print_result()
     
    # user need password
    si = SuShell('pwd', 'root')
    si.run()
    si.print_result()
