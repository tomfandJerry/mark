# PWN学习

## 基础知识

### 栈

#### 栈的定义

栈是一个后进先出（Last in First Out）的数据结构，其操作主要有压栈(push)和出栈(pop)两种操作

![ 栈的基本图片](D:\文件\学习文件\pwn学习\PWN学习笔记\图片\1.png)



高级语言在运行时都会被转换为汇编程序，在汇编程序运行过程中，充分利用了这一数据结构。每个程序在运行时都有虚拟地址空间，其中某一部分就是该程序对应的栈，用于保存函数调用信息和局部变量。此外，常见的操作也是压栈与出栈。需要注意的是，**程序的栈是从进程地址空间的高地址向低地址增长的**。

#### c语言函数调用栈

程序的执行过程可看作连续的函数调用。当一个函数执行完毕时，程序要回到调用指令的下一条指令(紧接call指令)处继续执行。函数调用过程通常使用堆栈实现，每个用户态进程对应一个调用栈结构(call stack)。编译器使用堆栈传递函数参数、保存返回地址、临时保存寄存器原有值(即函数调用的上下文)以备恢复以及存储本地局部变量。**不同处理器和编译器的堆栈布局、函数调用方法都可能不同，但堆栈的基本概念是一样的。**

在x86处理器中，**EIP(Instruction Pointer)是指令寄存器，指向处理器下条等待执行的指令地址(代码段内的偏移量)，每次执行完相应汇编指令EIP值就会增加。ESP(Stack Pointer)是堆栈指针寄存器，存放执行函数对应栈帧的栈顶地址(也是系统栈的顶部)，且始终指向栈顶；EBP(Base Pointer)是栈帧基址指针寄存器，存放执行函数对应栈帧的栈底地址**，用于C运行库访问栈中的局部变量和参数。

 注意，EIP是个特殊寄存器，不能像访问通用寄存器那样访问它，即找不到可用来寻址EIP并对其进行读写的操作码(OpCode)。EIP可被jmp、call和ret等指令隐含地改变(事实上它一直都在改变)。

**不同架构的CPU，寄存器名称被添加不同前缀以指示寄存器的大小。例如x86架构用字母“e(extended)”作名称前缀，指示寄存器大小为32位；x86_64架构用字母“r”作名称前缀，指示各寄存器大小为64位。**

**栈帧指针寄存器**

为了访问函数局部变量，必须能定位每个变量。局部变量相对于堆栈指针ESP的位置在进入函数时就已确定，理论上变量可用ESP加偏移量来引用，但ESP会在函数执行期随变量的压栈和出栈而变动。尽管某些情况下编译器能跟踪栈中的变量操作以修正偏移量，但要引入可观的管理开销。而且在有些机器上(如Intel处理器)，用ESP加偏移量来访问一个变量需要多条指令才能实现。

因此，许多编译器使用帧指针寄存器FP(Frame Pointer)记录栈帧基地址。局部变量和函数参数都可通过帧指针引用，因为它们到FP的距离不会受到压栈和出栈操作的影响。有些资料将帧指针称作局部基指针(LB-local base pointer)。

在Intel CPU中，寄存器BP(EBP)用作帧指针。在Motorola CPU中，除A7(堆栈指针SP)外的任何地址寄存器都可用作FP。当堆栈向下(低地址)增长时，以FP地址为基准，函数参数的偏移量是正值，而局部变量的偏移量是负值。

**寄存器使用约定**

程序寄存器组是唯一能被所有函数共享的资源。虽然某一时刻只有一个函数在执行，但需保证当某个函数调用其他函数时，被调函数不会修改或覆盖主调函数稍后会使用到的寄存器值。因此，IA32采用一套统一的寄存器使用约定，所有函数(包括库函数)调用都必须遵守该约定。

根据惯例，寄存器%eax、%edx和%ecx为主调函数保存寄存器(caller-saved registers)，当函数调用时，若主调函数希望保持这些寄存器的值，则必须在调用前显式地将其保存在栈中；被调函数可以覆盖这些寄存器，而不会破坏主调函数所需的数据。寄存器%ebx、%esi和%edi为被调函数保存寄存器(callee-saved registers)，即被调函数在覆盖这些寄存器的值时，必须先将寄存器原值压入栈中保存起来，并在函数返回前从栈中恢复其原值，因为主调函数可能也在使用这些寄存器。此外，被调函数必须保持寄存器%ebp和%esp，并在函数返回后将其恢复到调用前的值，亦即必须恢复主调函数的栈帧。

 当然，这些工作都由编译器在幕后进行。不过在编写汇编程序时应注意遵守上述惯例。



## 做题练习（CTFshow）

### ctfshow-pwn0

用shell工具连接到靶机，等待程序运行完成，即可获取到靶机的shell控制权限，然后进入根目录查看目录即可找到flag

### ctfshow-pwn1

这道题只要简单的nc连接上这台靶机即可给我们显示flag、

### ctfshow-pwn2

这道题只要简单的nc连接上这台靶机，然后输入cat ctfshow_flag即可获取到flag

### ctfshow-pwn3

 这道题就是简单的告诉我们哪个函数可以实现获取flag的操作

### ctfshow-pwn4

当输入“CTFshowPWN”后就能够得到我们所需要的shell了，进而就能拿到我们所需的flag。

### ctfshow-pwn5

使用NASM汇编器和ld链接器编译成可执行文件。

首先，将代码保存为一个文件，例如 Welcome_CTFshow.asm 。然后，使用以下命令将其编译为对

### ctfshow-pwn6

根据题目源码注释片段可以了解到立即寻址方式在哪，而且可以直接算出.

### ctfshow-pwn7

通过IDA看相关汇编代码得到结果

### ctfshow-pwn8

; 直接寻址方式
    mov ecx, msg      ; 将msg的地址赋值给ecx

### ctfshow-pwn9

; 寄存器间接寻址方式
    mov esi, msg        ; 将msg的地址赋值给esi
    mov eax, [esi]      ; 将esi所指向的地址的值赋值给eax

### ctfshow-pwn10

; 寄存器相对寻址方式
    mov ecx, msg        ; 将msg的地址赋值给ecx
    add ecx, 4          ; 将ecx加上4
    mov eax, [ecx]      ; 将ecx所指向的地址的值赋值给eax

### ctfshow-pwn11

; 基址变址寻址方式
    mov ecx, msg        ; 将msg的地址赋值给ecx
    mov edx, 2          ; 将2赋值给edx
    mov eax, [ecx + edx*2]  ; 将ecx+edx*2所指向的地址的值赋值给eax

### ctfshow-pwn12

; 相对基址变址寻址方式
    mov ecx, msg        ; 将msg的地址赋值给ecx
    mov edx, 1          ; 将1赋值给edx
    add ecx, 8          ; 将ecx加上8
    mov eax, [ecx + edx*2 - 6]  ; 将ecx+edx*2-6所指向的地址的值赋值给eax

### ctfshow-pwn13

这道题想让我们了解如何使用gcc将c语言程序编译成可执行文件，通过下面的指令即可

```
gcc flag.c -o 1
```

### ctfshow-pwn14

先观察c语言程序，发现他要先打开一个名为key的文件，读取里面内容，才能进行下一步，再联想到题目提示的key=CTFshow，所以我们在编译完成后还需要写个key文件，然后再运行才能得到flag，关键代码如下

```
gcc flag.c -o 1
echo "CTFshow" > key
./1
```

运行上述命令即可的到flag

### ctfshow-pwn15

这道题考验我们如何将汇编语言程序编译成可执行文件，具体用到了nasm和ld，具体命令如下

```
nasm -f elf flag.nasm #这个命令将会生成一个flag.o文件
ld -m elf_i386 -s -o flag flag.o #生成flag可执行文件
```

然后运行flag文件即可得到flag

### ctfshow-pwn16

这道题考验我们如何将.s文件编译成可执行文件，具体命令如下

```
gcc flag.s -o flag
./flag
```

即可获取到flag

象文件：

**nasm -f elf Welcome_to_CTFshow.asm**

这将生成一个名为 Welcome_CTFshow.o 的对象文件。接下来，使用以下命令将对象文件链接成可

执行文件：

**ld -m elf_i386 -s -o Welcome_to_CTFshow Welcome_to_CTFshow.o**

这将生成一个名为 Welcome_CTFshow 的可执行文件。

## Linux的相关知识

### 软连接

软连接是linux中一个常用命令，它的功能是为某一个文件在另外一个位置建立一个同步的链接。软连接类似与c语言中的指针，传递的是文件的地址；更形象一些，软连接类似于WINDOWS系统中的快捷方式。

例如，在a文件夹下存在一个文件hello，如果在b文件夹下也需要访问hello文件，那么一个做法就是把hello复制到b文件夹下，另一个做法就是在b文件夹下建立hello的软连接。通过软连接，就不需要复制文件了，相当于文件只有一份，但在两个文件夹下都可以访问。

创建软连接的方法需要使用下面的命令

```
ln  -s  [源文件或目录]  [目标文件或目录]
如下实例

ln –s  ./a/test  ./b/hello
它的作用是将当前路径下的a文件夹中的test文件，在当前路径的b文件夹中建立软连接，并且用一个新的名字为hello

```

### ElF文件相关知识

在`Linux`系统使用过程中，我们经常会看到`elf32-i386`、`ELF 64-bit LSB`等字样。那么究竟`ELF`是什么呢？



#### 几种常见的ELF文件

在`Linux`下，我们经`gcc编译`之后生成的可执行文件属于`ELF`文件：

![几种常见的ELF文件](https://atts.w3cschool.cn/attachments/image/20200803/1596436923144269.jpg)

`ELF`是一类文件类型，而不是特指某一后缀的文件。`ELF`（Executable and Linkable Format，可执行与可链接格式）文件格式，在`Linux`下主要有如下三种文件：



- **可执行文件（.out）**：`Executable File`，包含代码和数据，是可以直接运行的程序。其代码和数据都有固定的地址 （或相对于基地址的偏移 ），系统可根据这些地址信息把程序加载到内存执行。



- **可重定位文件（.o文件）**：`Relocatable File`，包含基础代码和数据，但它的代码及数据都没有指定绝对地址，因此它适合于与其他目标文件链接来创建可执行文件或者共享目标文件。



- **共享目标文件（.so）**：`Shared Object File`，也称动态库文件，包含了代码和数据，这些数据是在链接时被链接器（`ld`）和运行时动态链接器（`ld.so.l、libc.so.l、ld-linux.so.l`）使用的。

`ELF格式`可结构大致为：

![ELF格式结构](https://atts.w3cschool.cn/attachments/image/20200803/1596436984848957.jpg)

ELF文件由4部分组成，分别是ELF头（`ELF header`）、程序头表（`Program header table`）、节（`Section`）和节头表（`Section header table`）。

实际上，一个文件中不一定包含全部内容，而且它们的位置也未必如同所示这样安排，只有`ELF头`的位置是固定的，其余各部分的位置、大小等信息由`ELF头`中的各项值来决定。



#### readelf工具的使用

在`Linux`下，我们可以使用`readelf` 命令工具可以查看`ELF`格式文件的一些信息。下面我们先准备一个动态链接相关的demo：

![动态链接相关的demo](https://atts.w3cschool.cn/attachments/image/20200803/1596437291420581.jpg)

**文件1（main.c）**：



include "test.h"

```
int main(void)
{
    print_hello();
    return 0;
}
```

**文件2（test.c）**：



include "test.h"

void print_hello(void) { printf("hello world\n"); }

**文件3（test.h）**：

ifndef __TEST_H

```
#define __TEST_H


#include <stdio.h>


void print_hello(void);


#endif
```

执行相关命令生成相关文件：`.out文件`、`.o文件`、`.so文件`。如：

![执行相关命令生成相关文件](https://atts.w3cschool.cn/attachments/image/20200803/1596437440941645.jpg)

下面我们使用`readelf`命令来查看这三类文件的一些信息。`readelf`命令格式为：

readelf <option(s)> elf-file(s)



#### 查看可执行文件头部信息：

![可执行文件头部信息](https://atts.w3cschool.cn/attachments/image/20200803/1596437526118468.jpg)

查看可执行文件头部信息是，我们发现这样一个问题，头部信息中的类型竟然是共享库文件，而我们查看的是可执行文件，自相矛盾？

查了一些资料发现：`gcc编译`默认加了`--enable-default-pie`选项：

![gcc编译](https://atts.w3cschool.cn/attachments/image/20200803/1596437649432820.jpg)

`Position-Independent-Executable`是`Binutils`，`glibc`和`gcc`的一个功能，能用来创建介于共享库和通常可执行代码之间的代码–能像共享库一样可重分配地址的程序，这种程序必须连接到`Scrt1.o`。标准的可执行程序需要固定的地址，并且只有被装载到这个地址时，程序才能正确执行。`PIE`能使程序像共享库一样在主存任何位置装载，这需要将程序编译成位置无关，并链接为`ELF`共享对象。

引入`PIE`的原因是让程序能装载在随机的地址，通常情况下，内核都在固定的地址运行，如果能改用位置无关，那攻击者就很难借助系统中的可执行码实施攻击了。类似缓冲区溢出之类的攻击将无法实施。而且这种安全提升的代价很小。

也就是说，`pie`这是一种保护我们可执行程序的一种手段。这里我们只是做实验，我们可以加`-no-pie`参数先把`pie`给关掉：

![把pie给关掉](https://atts.w3cschool.cn/attachments/image/20200803/1596437719709379.jpg)

可以看到，类型终于对得上了。`ELF头部`信息还包含有`Entry point address`（入口地址）、`Start of program headers`（程序头的起始字节）、`Start of section headers`（节头的起始字节）等信息。



#### 查看可重定位文件头部信息：

![文件头部信息](https://atts.w3cschool.cn/attachments/image/20200803/1596437761339306.jpg)



#### 查看共享目标文件头部信息：

![共享目标文件](https://atts.w3cschool.cn/attachments/image/20200803/1596437831390478.jpg)

同样的，`readelf` 搭配其它参数可以查看`ELF文件`的其它信息：

![ELF文件的其它信息](https://atts.w3cschool.cn/attachments/image/20200803/1596437893538039.jpg)



#### objdump工具的使用

`objdump`工具用于显示一个或多个目标文件的信息。`objdump`命令格式：

objdump <option(s)> <file(s)>

可执行文件、可重定位文件与共享目标文件都属于目标文件，所以都可以使用这个命令来查看一些信息。



### 查看可重定位文件反汇编信息：

![可重定位文件反汇编信息](https://atts.w3cschool.cn/attachments/image/20200803/1596437962791114.jpg)



查看可执行文件反汇编信息：

![可执行文件反汇编信息](https://atts.w3cschool.cn/attachments/image/20200803/1596437998334156.jpg)



### 查看共享目标文件反汇编信息：

![共享目标文件反汇编信息](https://atts.w3cschool.cn/attachments/image/20200803/1596438033560876.jpg)

## 操作系统的相关知识

### fork()创建子进程

fork()函数：用于创建一个新的进程，创建的新进程是原来进程的子进程，创建的方法是将当前进程的内存内容完整的复制到内存的另一个区域（换句话说，原本的父进程执行到了代码的某个位置，fork()，创建的子进程也会从此位置开始执行，内存情况是完全相同的）。

返回值：如果子进程创建失败，返回值是-1。如果子进程创建成功，对于父进程而言，fork的返回值是子进程的pid（子进程的进程号）；对于子进程而言，fork的返回值是0。

由于fork的返回值在父子进程中是不同的，因此可以将fork的返回值作为if判断的条件，让父子进程执行不同的语句。

 fork会**将当前进程的内存内容完整的复制到内存的另一个区域**。因此创建的子进程和原本的父进程的内存空间是独立的，不会相互影响

 孤儿就是没有父母。换句话将，如果父进程1创建子进程后2，父进程1ger~了（结束），子进程2还在运行，那么这个子进程2就会沦为孤儿进程。此时子进程的父进程就会被挂在到系统0中，而不是原本的那个挂掉的父进程1

### waitpid函数

大家知道，当用fork启动一个新的子进程的时候，子进程就有了新的生命周期，并将在其自己的地址空间内独立运行。但有的时候，我们希望知道某一个自己创建的子进程何时结束，从而方便父进程做一些处理动作。同样的，在用ptrace去attach一个进程滞后，那个被attach的进程某种意义上说可以算作那个attach它进程的子进程，这种情况下，有时候就想知道被调试的进程何时停止运行。

以上两种情况下，都可以使用Linux中的waitpid()函数做到。先来看看waitpid函数的定义：

#include <sys/types.h> 
#include <sys/wait.h>
pid_t waitpid(pid_t pid,int *status,int options);
如果在调用waitpid()函数时，当指定等待的子进程已经停止运行或结束了，则waitpid()会立即返回；但是如果子进程还没有停止运行或结束，则调用waitpid()函数的父进程则会被阻塞，暂停运行。
下面来解释以下调用参数的含义：

1）pid_t pid

参数pid为欲等待的子进程识别码，其具体含义如下：


参数值	说明
pid<-1	等待进程组号为pid绝对值的任何子进程。
pid=-1	等待任何子进程，此时的waitpid()函数就退化成了普通的wait()函数。
pid=0	等待进程组号与目前进程相同的任何子进程，也就是说任何和调用waitpid()函数的进程在同一个进程组的进程。
pid>0	等待进程号为pid的子进程。
2）int *status

这个参数将保存子进程的状态信息，有了这个信息父进程就可以了解子进程为什么会推出，是正常推出还是出了什么错误。如果status不是空指针，则状态信息将被写入
器指向的位置。当然，如果不关心子进程为什么推出的话，也可以传入空指针。
Linux提供了一些非常有用的宏来帮助解析这个状态信息，这些宏都定义在sys/wait.h头文件中。主要有以下几个：
宏	说明
WIFEXITED(status)	如果子进程正常结束，它就返回真；否则返回假。
WEXITSTATUS(status)	如果WIFEXITED(status)为真，则可以用该宏取得子进程exit()返回的结束代码。
WIFSIGNALED(status)	如果子进程因为一个未捕获的信号而终止，它就返回真；否则返回假。
WTERMSIG(status)	如果WIFSIGNALED(status)为真，则可以用该宏获得导致子进程终止的信号代码。
WIFSTOPPED(status)	如果当前子进程被暂停了，则返回真；否则返回假。
WSTOPSIG(status)	如果WIFSTOPPED(status)为真，则可以使用该宏获得导致子进程暂停的信号代码。
3）int options

参数options提供了一些另外的选项来控制waitpid()函数的行为。如果不想使用这些选项，则可以把这个参数设为0。
主要使用的有以下两个选项：
参数	说明
WNOHANG	如果pid指定的子进程没有结束，则waitpid()函数立即返回0，而不是阻塞在这个函数上等待；如果结束了，则返回该子进程的进程号。
WUNTRACED	如果子进程进入暂停状态，则马上返回。
这些参数可以用“|”运算符连接起来使用。
如果waitpid()函数执行成功，则返回子进程的进程号；如果有错误发生，则返回-1，并且将失败的原因存放在errno变量中。
失败的原因主要有：没有子进程（errno设置为ECHILD），调用被某个信号中断（errno设置为EINTR）或选项参数无效（errno设置为EINVAL）
如果像这样调用waitpid函数：waitpid(-1, status, 0)，这此时waitpid()函数就完全退化成了wait()函数。

### execve函数

execve 本身并不是一个后门函数。实际上， execve 是一个标准的系统调用函数，用于在 Linux

和类 Unix 系统中执行一个新的程序。它的原型如下：

``` c
int execve(const char *filename, char *const argv[], char *const envp[]);
```

该函数接受三个参数：

1. filename ：要执行的程序的文件名或路径。
2. argv ：一个以 NULL 结尾的字符串数组，表示传递给新程序的命令行参数。
3. envp ：一个以 NULL 结尾的字符串数组，表示新程序的环境变量。

当调用 execve 函数时，它会将当前进程替换为新程序的代码，并开始执行新程序。新程序接收

argv 和 envp 作为命令行参数和环境变量。

在加入某些参数后就可以达到我们所需要的后门函数的效果。

## 编译与链接器

### NASM和MASM汇编器

、NASM 命令选项
(1)、-f 指定输出文件的格式
NASM 生成的文件只包含“纯二进制”的内容，

C:\>nasm -f bin hello.asm 
输出的二进制文件名为hello(无扩展名)。

如果您没有向NASM提供-f选项，它将为您自己选择输出文件格式。

在NASM的发行版中，默认值始终是bin。

上面的指令和下面的指令等价的

C:\>nasm  hello.asm 
(2)、-o 指定编译后输出的文件名
-o 指定编译后输出（Output）的文件名

```
C:\>nasm -f bin hello.asm -o hello.bin
```


输出的二进制文件名为hello.bin

(3)、-l 指定输出文件的格式
C:\>nasm hello.asm -l hello.lst

生成二进制文件hello和listing文件，这个listing文件是什么样的？直接看看

📚 hello.asm文件

	start	mov ax,1
			mov bx,2
			times 32 db 0xc
	current	times 510-(current-start) db 0
			db 0x55,0xaa

📚 hello.lst文件

     1 00000000 B80100                  start	mov ax,1
     2 00000003 BB0200                  		mov bx,2
     3 00000006 0C<rept>                		times 32 db 0xc
     4 00000026 00<rept>                current	times 510-(current-start) db 0
     5 000001FE 55AA                    		db 0x55,0xaa

在源文件的左面加上了机器码和汇编地址

(4)、-h 查看帮助
C:\>nasm -help
1
二、MASM
三、NASM & MASM 使用&区别
3.1、标号
MASM中 通过offset取得标号的段内偏移地址

label1:
		mov ax,offset label1		;// 相当于mov ax,0
label2:
		mov ax,offset label2		;// 相当于mov ax,3，因为上条指令长度为3

NASM中直接使用标号

label1:
		mov ax,label1				;// 相当于mov ax,0
label2:
		mov ax,label2				;// 相当于mov ax,3，因为上条指令长度为3

寻址方式
MASM

mov ax,cs:[di]
NASM

mov ax,[cs:di]

### ld链接器

. ld 的基本使用
3.1 链接目标文件生成可执行文件
使用 ld 命令可以将目标文件链接成可执行文件。假设你有两个目标文件 file1.o 和 file2.o，可以使用以下命令进行链接：

ld file1.o file2.o -o myprogram

3.2 指定输出文件
使用 -o 选项可以指定输出文件的名称。例如，将输出文件命名为 output：

ld file1.o file2.o -o output

3.3 链接共享库
使用 -l 选项可以链接共享库。例如，链接标准 C 库（libc）：

ld file1.o file2.o -o myprogram -lc
还可以指定库搜索路径，使用 -L 选项。例如，添加 /usr/local/lib 作为库搜索路径：

ld file1.o file2.o -o myprogram -L/usr/local/lib -lc
4. ld 的高级功能
4.1 使用链接脚本
链接脚本（linker script）可以定制链接过程。使用 -T 选项指定链接脚本。例如，使用 linker.ld 脚本：

ld -T linker.ld file1.o file2.o -o myprogram
一个简单的链接脚本示例：

SECTIONS
{
  . = 0x10000;
  .text : { *(.text) }
  .data : { *(.data) }
  .bss : { *(.bss) }
}

4.2 生成共享库
使用 -shared 选项可以生成共享库。例如，生成 libmylib.so：

ld -shared -o libmylib.so file1.o file2.o

4.3 结合其他工具使用
ld 可以与其他工具结合使用，如 gcc、as 等。例如，可以使用 gcc 编译 C 代码并链接生成可执行文件：

gcc -c main.c
ld main.o -o myprogram -lc

5. ld 参数详解
ld 提供了丰富的参数，可以帮助你定制链接过程。以下是一些常用参数的详解：

-o <file>：指定输出文件的名称。
-l <library>：链接指定的库。
-L <dir>：指定库搜索路径。
-T <script>：使用指定的链接脚本。
-shared：生成共享库。
-static：生成静态链接的可执行文件。
-r：生成可重定位的目标文件。
-Map <file>：生成链接映射文件。
-e <entry>：指定入口点。
--start-group 和 --end-group：指定库组，以解决循环依赖。
--version：显示版本信息。
--help：显示帮助信息。
6. ld 常见问题及解决方法
问题一：无法找到库文件
如果 ld 无法找到库文件，可能是因为库搜索路径不正确。请确保库文件位于指定的搜索路径中，并使用 -L 选项添加库搜索路径：

ld file1.o file2.o -o myprogram -L/usr/local/lib -lc
1
问题二：未定义的符号
如果链接过程中出现未定义的符号错误，可能是因为缺少必要的目标文件或库文件。请确保所有必要的文件都已包含在链接命令中：

ld file1.o file2.o -o myprogram -lc

**我常用的指令 ld -m elf_i386 -s -o 1 1.o**



### GCC

gcc的基本语法是：

gcc [options] [filenames]
1
其中[options]表示参数，[filenames]表示相关文件的名称。
一些常用的参数及含义下表所示：

参数名称	含义
-E	仅执行预处理，不进行编译、汇编和链接（生成后缀为 .i 的预编译文件）
-S	执行编译后停止，不进行汇编和链接（生成后缀为 .s 的预编译文件）
-c	编译程序，但不链接成为可执行文件（生成后缀为 .o 的文件）
-o	直接生成可执行文件
-O/-O1/-O2/-O3	优化代码，减少代码体积，提高代码效率，但是相应的会增加编译的时间
-Os	优化代码体积（多个-O参数默认最后一个）
-Og	代码优化（不能与“-O”一起用）
-O0	关闭优化
-l [lib]	（这里是小写的L，命令无中括号，下同）指定程序要链接的库，[lib]为库文件名称。如果gcc编译选项中加入了“-static”表示寻找静态库文件
-L [dir]	指定-l（小写-L）所使用到的库文件所在路径
-I [dir]	（这里是大写的I）增加 include 头文件路径
-D [define]	预定义宏
-static	链接静态库生成目标文件，禁止使用动态库（在支持动态链接的系统上）
-share	尽量使用动态库，但前提是系统存在动态库，生成的目标文件较小
-shared	生成共享文件，然后可以与其它文件链接生成可执行文件
-fpic	生成适用于共享库的与地址无关的代码（PIC）（如果机器支持的话）
-fPIC	生成与位置无关的的代码，适用于使用动态库，与“-fpic”的区别在于去除去全局偏移表的任何限制（如果机器支持的话）
-fPIE	使用与地址无关的代码生成可执行文件
-w	不输出任何警告信息
-Wall	开启编译器的所有警告选项
-g	生成调试信息，方便gdb调试
-v	查看gcc编译器的版本，显示gcc执行时的详细过程
-ggdb	加入GDB调试器能识别的格式
-Werror	将所有的警告当成错误进行处理，在所有产生警告的地方停止编译
-M	生成适合于make规则的主要文件的依赖信息
-MM	与“-M”相比忽略由“#include”所造成的依赖
-MD	与-M作用类似，将输出导入到 .d 文件中
-MMD	与-MM作用类似，将输出导入到 .d 文件中
–help	查看帮助信息（注意前面是两个“-”，一个“-”不行）
–version	查看版本信息（注意前面是两个“-”，一个“-”不行）
四、gcc编译C语言过程示例
首先创建一个hello.c文件作为实例


要编译这个程序，只要在命令行下执行如下命令：

gcc hello.c -o hello
./hello
这样，gcc 编译器会生成一个名为hello的可执行文件，然后执行./hello就可以看到程序的输出结果了。


命令行中 gcc表示用gcc来编译源程序，hello.c是源程序文件，-o hello选项表示要求编译器输出的可执行文件名为hello。从程序员的角度看，只需简单地执行一条gcc命令就可以了；但从编译器的角度来看，却需要完成一系列非常繁杂的工作。首先，gcc需要调用预处理程序cpp，由它负责展开在源文件中定义的宏，并向其中插入#include语句所包含的内容；接着，gcc会调用ccl和as将处理后的源代码编译成目标代码；最后，gcc会调用链接程序ld，把生成的目标代码链接成一个可执行程序。



为了更好地体现gcc的工作过程，可以把上述编译过程分成预处理(Pre-Processing)、编译(Compiling)、汇编(Assembling)、链接(Linking) 四个步骤单独进行，并观察每步的运行结果。

Step1：预处理
预处理通过对宏定义(像#define）进行展开，对头文件（像 stdio.h）进行展开，对条件进行（像ifdef）编译，展开所有宏，删除所有注释（像"//"）。预处理cpp把源代码以及头文件预编成一个.i文件。命令如下：

gcc -E hello.c -o hello.i

gcc的-E参数，可以让编译器在预编译后停止，并输出预编译结果（hello.i文件）。



此时若查看hello.i文件中的内容，会发现stdio.h的内容确实都插到文件里去了，而且被预处理的宏定义也都作了相应的处理。



注意：这时并不检查语法，所以即使有语法错误也不会报错。

Step2：编译
编译也就是检查语法是否错误，将预处理过的文件编译成汇编（.s）文件。命令如下：

gcc -S hello.i -o hello.s




Step3：汇编
汇编也就是将汇编（.s）文件生成目标文件（二进制文件）。通过汇编，文本代码变成了二进制代码（二进制代码文件以.o为后缀名）。命令如下：

gcc -c hello.s -o hello.o

打开hello.o文件，是一堆乱码，因为.o文件为二进制文件。



Step4：链接
链接过程就是找到依赖的库文件（静态与动态），将目标文件链接为可执行程序。命令如下：

gcc [目标文件] -o [可执行程序] -l[动态库名]
假如没有动态库的话，直接使用以下命令：

gcc [目标文件] -o [可执行程序]

对于本例，则输入命令如下：

gcc hello.o -o hello
## 汇编语言的相关知识

.s 文件是汇编语言源文件的一种常见扩展名。它包含了使用汇编语言编写的程序代码。汇编语言

是一种低级编程语言，用于直接操作计算机的指令集架构。 .s 文件通常由汇编器（Assembler）处

理，将其转换为可执行文件或目标文件。

可以使用 gcc 命令直接编译汇编语言源文件（ .s 文件）并将其链接为可执行文件。 gcc 命令具

有适用于多种语言的编译器驱动程序功能，它可以根据输入文件的扩展名自动选择适当的编译器和链接

器。

```
gcc flag.s -o flag
```



## 其他知识

### 那system(“/bin/sh”);的工作原理是什么

system()函数先fork一个子进程，在这个子进程中调用/bin/sh -c来执行command指定的命

令。/bin/sh在系统中一般是个软链接，指向dash或者bash等常用的shell，-c选项是告诉shell从字符串

command中读取要执行的命令（shell将扩展command中的任何特殊字符）。父进程则调用waitpid()函

数来为变成僵尸的子进程收尸，获得其结束状态，然后将这个结束状态返回给system()函数的调用者。

那么也就是说执行完这个后它就会返回一个shell给函数的调用者

也就达到了远程命令执行的效果了，读取flag只需要执行“cat /ctfshow_flag”命令即可

system(“cat /ctfshow_flag”);

system(“/bin/sh”);这一类的我们称之为后门函数，再后续利用过程中我们要尽可能找到或者构造出

来







