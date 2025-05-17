# Amigo-auto
Free soft to join waitlist in amigo
![image](https://github.com/user-attachments/assets/941340c8-bb92-4ae0-a5dd-9c3b6ea54f14)

софт регистрируется в вейт листе по почте и твиттеру, для твиттеров нужны только токены, для почты, нужно, чтобы на ней был включен IMAP, либо чтобы письма пересылались на почту с аймапом

**Для запуска:**

1. установить гит - гайд здесь: [клик](https://teletype.in/@magnifier01chin/8iwREMa30Kq)
2. заходим в папку с софтом и запускаем `INSTALL.bat`
3. заполняем данные в `configs`:

       configs/proxies.txt - сюда прокси в формате username:password@ip:port

       configs/x_tokens.txt - сюда токены от твиттер аккаунтов

       configs/emails.txt - почты: только адреса, если с них включена переадресация если нет, то: 'адрес:пароль'

**Настройка работы софта:**

в configs/config.py настраивается сама работа:

`DELAY_BETWEEN_ACCOUNTS` - тут можно указать паузу между аккаунтами аккаунтами, например:

        DELAY_BETWEEN_ACCOUNTS = (20, 30)
        
значит, что будет следующий аккаунт будет запускаться через 20-30 секунд после предыдущего

        SINGLE_IMAP_ACCOUNT

ставим `True`, если включена переадресация на одну почту, `False`, если переадресации нет и письмо будет приходить только на саму почту


*если включена переадресация, то данные будут браться со следующих строк:*

        SINGLE_EMAIL = "loveAbstract@MagniFier01Chin"
        SINGLE_APP_PASSWORD = "abcd-efgh-ijkl-mnop"
        SINGLE_IMAP_SERVER = "imap.mail.me.com"
        SINGLE_IMAP_PORT = 993

если нет, то имеет данные берутся отсюда, если это ваш случай, заполняем их:

        IMAP_SERVER = "imap.rambler.ru"
        IMAP_PORT = 993

мой тг: [@MagniFier01Chin](https://t.me/MagniFier01Chin) помощь/вопросы

мой канал: [@povedalcrypto](https://t.me/povedalcrypto) апдейты/идеи
