# flake8: noqa: F841
import ssl
import socket
import discord
import dns
from cryptography import x509
from urllib.parse import urlparse
import requests
from scapy.layers.inet import traceroute
import aiohttp
import os
import asyncio
from bs4 import BeautifulSoup
import json
import io
from discord.ext import Embed, commands, File
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes


with open('config.json') as f:
    config = json.load(f)


GLOBAL_FOOTER = config.get('global_footer')
GIF_URL = config.get('gif_url')
COOLDOWN_DURATION = config.get('cooldown_duration')


# Does a large variety of website related commands


blocked_dns_services = {
    "AdGuard": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["94.140.14.14", "94.140.15.15"]
    },
    "AdGuard Family": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["94.140.14.15", "94.140.15.16"]
    },
    "CleanBrowsing Adult": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["185.228.168.10", "185.228.169.11"]
    },
    "CleanBrowsing Family": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["185.228.168.168", "185.228.169.168"]
    },
    "CleanBrowsing Security": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["185.228.168.9", "185.228.169.9"]
    },
    "CloudFlare": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["1.1.1.1", "1.0.0.1"]
    },
    "CloudFlare Family": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["1.1.1.3", "1.0.0.3"]
    },
    "Comodo Secure": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["8.26.56.26", "8.20.247.20"]
    },
    "Google DNS": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["8.8.8.8", "8.8.4.4"]
    },
    "Neustar Family": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["156.154.70.1", "156.154.71.1"]
    },
    "Neustar Protection": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["156.154.70.3", "156.154.71.3"]
    },
    "Norton Family": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["199.85.126.10", "199.85.127.10"]
    },
    "OpenDNS": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["208.67.222.222", "208.67.220.220"]
    },
    "OpenDNS Family": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["208.67.222.123", "208.67.220.123"]
    },
    "Quad9": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["9.9.9.9", "149.112.112.112"]
    },
    "Yandex Family": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["77.88.8.8", "77.88.8.1"]
    },
    "Yandex Safe": {
        "status": "<a:green:1254732116814462977> Not Blocked",
        "nameservers": ["77.88.8.88", "77.88.8.2"]
    }
}


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/113.0',
    'Connection': 'keep-alive',
    'Cookie': 'cookie_consent_functional=allow; cookie_consent_analytical=allow; cf_clearance=nTDfHEP4FdCVVTbv._XhBTHMmnG7bRIAU2k1yLjikw8-1687783804-0-250; XSRF-TOKEN=eyJpdiI6IlV1Z0Q4cVVscHljSHR1dVJoZXdzQkE9PSIsInZhbHVlIjoiNnFqOVwvUkVNVFl4WHptY0ZpR2d5QkNFN21FSnNqWHBYZ1R5ZXpTNGlKVXVqM1RDUExGeXZKN2JyczJuXC8rSFp0IiwibWFjIjoiMWVhYmY5NDIwNDkyOGJmYmVkZDc1YzU1MDA0ZTExNjE5ZjRiYmU5MDU4NzY4MWMyYjg4ZDkzYjE2YTU2OTJjNCJ9; abuseipdb_session=eyJpdiI6ImtuOGhtK3p1Ym5vOFQ4Q1FKSXd0QUE9PSIsInZhbHVlIjoiK2pkQW1udVRlZVJVeGJwUXBhTVNNYXVKUU95d1dPcHVOT3ZwQWV2WXNycEF3dnIrZDB6a0FHeWVtMnQrcXRzRSIsIm1hYyI6ImMyYjQwOTU0Y2IzY2RmODJlMTY0ZDE1MDVmZDNkMTAyYWY4NmE1MmY2ZjI0YTY1ZTY4ZThmZjk2MWYzZWQ5YTIifQ%3D%3D'
}


directory_list = [
    'robots.txt', 'search/', 'admin/', 'login/', 'sitemap.xml', 'sitemap2.xml',
    'config.php', 'wp-login.php', 'log.txt', 'update.php', 'INSTALL.pgsql.txt',
    'user/login/', 'INSTALL.txt', 'profiles/', 'scripts/', 'LICENSE.txt',
    'CHANGELOG.txt', 'themes/', 'includes/', 'misc/', 'user/logout/', 'user/register/',
    'cron.php', 'filter/tips/', 'comment/reply/', 'xmlrpc.php', 'modules/', 'install.php',
    'MAINTAINERS.txt', 'user/password/', 'node/add/', 'INSTALL.sqlite.txt', 'UPGRADE.txt',
    'INSTALL.mysql.txt', 'config/', 'backup/', 'admin/config/', 'admin/maintenance/',
    'error_log', 'private/', 'uploads/', 'data/', 'tmp/', 'cache/', 'db/', 'logs/',
    'reports/', 'api/', 'admin/user/', 'admin/reports/', 'admin/settings/',
    'admin/tools/', 'user/settings/', 'user/profile/', 'user/notifications/',
    'admin/dashboard/', 'admin/notifications/', 'admin/roles/', 'admin/users/',
    'admin/themes/', 'admin/plugins/', 'admin/extensions/', 'admin/widgets/',
    'admin/multisite/', 'admin/multisite/settings/', 'admin/multisite/users/',
    'admin/multisite/themes/', 'admin/multisite/plugins/', 'admin/multisite/extensions/',
    'admin/multisite/widgets/', 'admin/maintenance/logs/', 'admin/maintenance/backups/',
    'admin/maintenance/config/', 'admin/maintenance/reports/', 'user/', 'login', 'admin/config',
    'admin/maintenance', 'private', 'uploads', 'data', 'tmp', 'cache', 'db', 'logs',
    'reports', 'api', 'admin/user', 'admin/reports', 'admin/settings', 'admin/tools',
    'user/settings', 'user/profile', 'user/notifications', 'admin/dashboard',
    'admin/notifications', 'admin/roles', 'admin/users', 'admin/themes', 'admin/plugins',
    'admin/extensions', 'admin/widgets', 'admin/multisite', 'admin/multisite/settings',
    'admin/multisite/users', 'admin/multisite/themes', 'admin/multisite/plugins',
    'admin/multisite/extensions', 'admin/multisite/widgets', 'admin/maintenance/logs',
    'admin/maintenance/backups', 'admin/maintenance/config', 'admin/maintenance/reports',
    'README.md', 'setup.php', 'db.sql', 'api.php', 'files/', 'setup/', 'install/',
    'data/', 'archive/', 'dumps/', 'old/', 'temp/', 'admin/assets/', 'admin/images/',
    'admin/js/', 'admin/css/', 'admin/fonts/', 'admin/videos/', 'admin/docs/',
    'admin/templates/', 'admin/updates/', 'admin/files/', 'admin/backups/'
]


async def ssl_certificate(ctx, url):
    try:
        hostname = urlparse(url).hostname
        ctx_ssl = ssl.create_default_context()
        with ctx_ssl.wrap_socket(socket.socket(), server_hostname=hostname) as ssock:
            ssock.connect((hostname, 443))
            der_cert = ssock.getpeercert(binary_form=True)
            x509_cert = x509.load_der_x509_certificate(der_cert)

            issuer = x509_cert.issuer
            issuer_parts = [
                f"Country: {issuer.get_attributes_for_oid(x509.NameOID.COUNTRY_NAME)[0].value}",
                f"Org: {issuer.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)[0].value}",
                f"Name: {issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value}"
            ]
            issuer_str = "\n".join(issuer_parts)

            expiry = x509_cert.not_valid_after_utc.strftime('%b %d %H:%M:%S %Y GMT')
            renewed = x509_cert.not_valid_before_utc.strftime('%b %d %H:%M:%S %Y GMT')
            serial_number = x509_cert.serial_number
            fingerprint = x509_cert.fingerprint(hashes.SHA256()).hex().upper()
            fingerprint = ':'.join(fingerprint[i:i + 2] for i in range(0, len(fingerprint), 2))

            asn1_curve = 'N/A'
            nist_curve = 'N/A'

            public_key = x509_cert.public_key()
            if isinstance(public_key, ec.EllipticCurvePublicKey):
                asn1_curve = public_key.curve.name
                nist_curve = get_nist_curve_name(asn1_curve)

            embed = discord.Embed(title=f"SSL Certificate Details for {url}", color=discord.Color.blue())
            embed.add_field(name="Issuer", value=issuer_str, inline=False)
            embed.add_field(name="Time", value=f"Expiry: {expiry}\nRenewed: {renewed}", inline=False)
            embed.add_field(name="Info", value=f"Serial Number: {serial_number}\nFingerprint: {fingerprint}\nASN1 Curve: {asn1_curve}\nNIST Curve: {nist_curve}", inline=False)

            embed.set_footer(text=GLOBAL_FOOTER)
            embed.set_image(url=GIF_URL)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f'Error fetching SSL certificate: {str(e)}')


async def dns_records(ctx, url):
    try:
        hostname = urlparse(url).hostname
        resolver = dns.resolver.Resolver()
        records = resolver.resolve(hostname, 'A')
        ip_addresses = [rdata.to_text() for rdata in records]

        # Create an embed
        embed = discord.Embed(title=f"DNS Records for {url}", color=discord.Color.green())
        embed.add_field(name="Name", value=hostname, inline=False)
        embed.add_field(name="IP Addresses", value="\n".join(ip_addresses), inline=False)

        embed.set_footer(text=GLOBAL_FOOTER)
        embed.set_image(url=GIF_URL)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f'Error fetching DNS records: {str(e)}')


async def server_status(ctx, url):
    try:
        response = requests.get(url)
        embed = discord.Embed(title=f"Server Status for {url}", color=discord.Color.green())
        if response.status_code == 200:
            embed.add_field(name="Status", value=f'{url} is up and running <a:green:1254732116814462977>.', inline=False)
        else:
            embed.add_field(name="Status", value=f'{url} <a:red:1254732135101894657> Returned status code: {response.status_code}', inline=False)
        embed.set_footer(text=GLOBAL_FOOTER)
        embed.set_image(url=GIF_URL)
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(title=f"Server Status for {url}", color=discord.Color.red())
        embed.add_field(name="Error", value=f'<a:red:1254732135101894657>Error checking server status: {str(e)}', inline=False)
        embed.set_footer(text=GLOBAL_FOOTER)
        embed.set_image(url=GIF_URL)
        await ctx.send(embed=embed)


async def blocked_list(ctx, url):
    try:
        results = {}
        for service, config in blocked_dns_services.items():
            resolver = dns.resolver.Resolver()
            resolver.nameservers = config["nameservers"]

            try:
                results = resolver.query(url)
                results[service] = config["status"]
            except dns.resolver.NXDOMAIN:
                results[service] = "<a:red:1254732135101894657> Blocked"

        embed = discord.Embed(title=f"Blocked Status for {url}", color=discord.Color.orange())
        for service, status in results.items():
            embed.add_field(name=service, value=status, inline=False)
        embed.set_footer(text=GLOBAL_FOOTER)
        embed.set_image(url=GIF_URL)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f'Error checking blocked list: {str(e)}')


async def hsts_check(ctx, url):
    try:
        response = requests.head(url)
        headers = response.headers
        if 'strict-transport-security' in headers:
            message = f'{url} <a:green:1254732116814462977>has HSTS enabled.<a:green:1254732116814462977>'
        else:
            message = f'{url} <a:red:1254732135101894657>does not have HSTS enabled.<a:red:1254732135101894657>'

        embed = discord.Embed(title="HSTS Check", description=message, color=discord.Color.purple())
        embed.set_footer(text=GLOBAL_FOOTER)
        embed.set_image(url=GIF_URL)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f'Error checking HSTS: {str(e)}')


async def traceroute_check(ctx, url):
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        if not hostname:
            await ctx.send('Invalid URL format. Please provide a valid URL.')
            return

        trace_result, _ = traceroute(hostname, maxttl=50, verbose=0, timeout=5, retry=-2)

        trace = []
        for sent, received in trace_result:
            if received.src:
                hop_ip = received.src
                try:
                    hop_hostname = socket.gethostbyaddr(hop_ip)[0]
                except (socket.herror, OSError):
                    hop_hostname = hop_ip
                trace.append(f"{hop_hostname} [{hop_ip}]")

        embed = discord.Embed(title=f"Traceroute Results for {hostname}", color=discord.Color.blue())

        if trace:
            embed.add_field(name="Traceroute Output", value="```\n" + "\n".join(trace) + "\n```", inline=False)
        else:
            embed.add_field(name="Traceroute Output", value="Sorry! I could not follow the route.", inline=False)

        embed.set_footer(text=GLOBAL_FOOTER)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f'Error during traceroute: {str(e)}')


def get_nist_curve_name(asn1_curve):
    curve_mapping = {
        'prime256v1': 'P-256',
        'secp384r1': 'P-384',
        'secp521r1': 'P-521'
    }
    return curve_mapping.get(asn1_curve, 'Unknown')


async def scrape_proxies(session, protocol='socks5'):
    api_url = f'https://api.proxyscrape.com/v2/?request=getproxies&protocol={protocol}&timeout=10000&country=all&ssl=all&anonymity=all&simplified=true'
    async with session.get(api_url) as response:
        if response.status != 200:
            return []
        proxies = await response.text()
        proxies = proxies.split('\r\n')
        proxies = list(filter(lambda proxy: len(proxy) > 0, proxies))
        return proxies


async def scrape_proxy_info(session, proxy):
    api_url = f'https://api.proxyscrape.com/v2/?request=proxyinfo&proxy={proxy}'
    async with session.get(api_url) as response:
        if response.status != 200:
            return None
        info = await response.text()
        return info.strip()


async def run_scraping(ctx, usage, url):
    async with aiohttp.ClientSession() as session:
        if usage.upper() == 'SCRAPE':
            protocol = url.split('://')[0]
            proxies_list = await scrape_proxies(session, protocol=protocol)

            if proxies_list:
                total_proxies = len(proxies_list)
                result_message = "\n".join(proxies_list)
                file_name = f"{url.split('://')[1].replace('/', '-').replace('.', '-')}.txt"
                file_path = os.path.join(r'C:\Users\Lego8\LegoHitsYou\proxys', file_name)

                with open(file_path, 'w') as file:
                    file.write(result_message)

                await ctx.send(f"Scraping Complete! Saved {total_proxies} proxies to file.", file=discord.File(file_path))
            else:
                await ctx.send(embed=discord.Embed(description="Error! Please try again.", color=0xff0000))

        elif usage.upper() == 'PROXYS':
            file_name = f"Proxyinfo-{url.split('://')[1].replace('/', '-').replace('.', '-')}.txt"
            file_path = os.path.join(r'C:\Users\Lego8\LegoHitsYou\proxys', file_name)

            info_messages = []
            for proxy in proxies_list:
                info = await scrape_proxy_info(session, proxy)
                if info:
                    info_messages.append(f"Proxy: {proxy}\n{info}\n")

            if info_messages:
                result_message = "\n".join(info_messages)

                with open(file_path, 'w') as file:
                    file.write(result_message)

                await ctx.send(
                    "Proxy Info Complete! Saved to file.",
                    file=discord.File(file_path),
                )
            else:
                await ctx.send(embed=discord.Embed(description="Error! Please try again.", color=0xff0000))


async def extract_subdomains(url):
    try:
        response = requests.get(f"https://www.abuseipdb.com/whois/{url}", headers=headers, verify=True)
        await asyncio.sleep(2)

        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')

            subdomains_header = soup.find('h4', string='Subdomains')

            if subdomains_header:
                subdomains = subdomains_header.find_next('ul').find_all('li')
                subdomain_list = [subdomain.text for subdomain in subdomains]
                return subdomain_list

            else:
                return []

        else:
            raise requests.HTTPError(f"The CDN blocked us!: {response.status_code}")

    except Exception as e:
        raise e


async def fetch_and_send_subdomains(ctx, url):
    try:
        subdomains = await Website.extract_subdomains(url)

        embed = discord.Embed(title=f"Subdomains for {url}", color=discord.Color.gold())
        embed.add_field(name="Subdomains", value="\n".join(subdomains) if subdomains else "No subdomains found.", inline=False)
        embed.set_footer(text="From PortLords w Love © 2024 | Version: 1.5.1")
        embed.set_image(url=GIF_URL)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f'Error fetching subdomains: {str(e)}')


async def check_cloudflare(ctx, url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://dnschecker.org/#A/{url}", headers=headers) as response:
                if response.status == 200:
                    text = await response.text()
                    soup = BeautifulSoup(text, 'html.parser')

                    # Check for Cloudflare in the results
                    cloudflare_detected = "cloudflare" in text.lower()

                    if cloudflare_detected:
                        await ctx.send(f"{url} is using CloudFlare!")
                    else:
                        await ctx.send(f"{url} is not using CloudFlare.")
                else:
                    await ctx.send(f"Error checking CloudFlare status for {url}: Status Code {response.status}")

    except Exception as e:
        await ctx.send(f"Error checking CloudFlare status for {url}: {str(e)}")


async def check_http_security(ctx, url):
    hdr = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
        "Cookie": "mkt=en-US;ui=en-US;SRCHHPGUSR=NEWWND=0&ADLT=DEMOTE&NRSLT=50",
        "Accept-Language": "en-us,en"
    }

    try:
        req = requests.get(url, headers=hdr)
        headers = req.headers

        messages = []

        try:
            xssprotect = headers['X-XSS-Protection']
            if xssprotect != '1; mode=block':
                messages.append(f'X-XSS-Protection not set properly, XSS may be possible: {xssprotect}')
        except KeyError:
            messages.append('X-XSS-Protection not set, XSS may be possible')

        try:
            contenttype = headers['X-Content-Type-Options']
            if contenttype != 'nosniff':
                messages.append(f'X-Content-Type-Options not set properly: {contenttype}')
        except KeyError:
            messages.append('X-Content-Type-Options not set')

        try:
            hsts = headers['Strict-Transport-Security']
        except KeyError:
            messages.append('HSTS header not set, MITM attacks may be possible')

        try:
            csp = headers['Content-Security-Policy']
            messages.append(f'Content-Security-Policy set: {csp}')
        except KeyError:
            messages.append('Content-Security-Policy missing')

        if messages:
            await ctx.send('\n'.join(messages))
        else:
            await ctx.send('All security headers are properly set.')

    except requests.exceptions.RequestException as e:
        await ctx.send(f'Error fetching URL: {e}')


async def find_website(ctx, url):
    if not url:
        await ctx.send("Please provide a website URL.")
        return

    await ctx.send("Finding website information...")
    try:
        data = {"remoteAddress": url}
        response = requests.post("https://domains.yougetsignal.com/domains.php", data=data).text
        response_data = json.loads(response)

        if "domainArray" in response_data:
            domain_list = "\n".join([i[0] for i in response_data["domainArray"]])
            embed = discord.Embed(title="Found Domains", description=domain_list, color=0x00ff00)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No domains found for the provided URL.")
    except json.JSONDecodeError:
        await ctx.send("Failed to decode the server response.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


async def check_website_directories(ctx, url):
    found_results = []
    failed_results = []

    for directory in directory_list:
        await asyncio.sleep(0.05)
        http = requests.get(f"{url}/{directory}")
        if http.status_code == 200:
            found_results.append(f"Here is {url} >> {directory}")
            file_url = f"{url}/{directory}"
            try:
                file_content = requests.get(file_url).content
                file = File(io.BytesIO(file_content), filename=directory)
                await ctx.send(file=file)
            except Exception as e:
                found_results.append(f"Failed to send file {file_url}: {e}")
        else:
            failed_results.append(f"Failed to get {url} >> {directory}")

    def chunk_text(text, max_length=2048):
        return [text[i:i + max_length] for i in range(0, len(text), max_length)]

    def create_embed(title, description, footer, image_url):
        embed = Embed(title=title, description=description, color=0x00ff00)
        embed.set_footer(text=footer)
        embed.set_image(url=image_url)
        return embed

    if found_results or failed_results:
        base_embed = create_embed(f"Directory Check Results for {url}", "", GLOBAL_FOOTER, GIF_URL)

        found_chunks = chunk_text("\n".join(found_results))
        failed_chunks = chunk_text("\n".join(failed_results))

        for chunk in found_chunks:
            embed = base_embed.copy()
            embed.description = f"Successful Results:\n{chunk}"
            try:
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Failed to send embed: {e}")

        for chunk in failed_chunks:
            embed = base_embed.copy()
            embed.description = f"failed Results:\n{chunk}"
            try:
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"Failed to send embed: {e}")


class Website(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='website', help='*`Look up information for website depending on usage`* **whitelist**')
    @commands.cooldown(1, COOLDOWN_DURATION, commands.BucketType.user)
    async def website(self, ctx, usage, url=None):
        if usage.upper() == 'SSL':
            await ssl_certificate(ctx, url)
        elif usage.upper() == 'DNS':
            await dns_records(ctx, url)
        elif usage.upper() == 'STATUS':
            await server_status(ctx, url)
        elif usage.upper() == 'BLOCKED':
            await blocked_list(ctx, url)
        elif usage.upper() == 'HSTS':
            await hsts_check(ctx, url)
        elif usage.upper() == 'TRACEROUTE':
            await traceroute_check(ctx, url)
        elif usage.upper() in 'SCRAPE' or usage.upper() == 'PROXYS':
            await run_scraping(ctx, usage, url)
        elif usage.upper() == 'SUBDOMAINS':
            await fetch_and_send_subdomains(ctx, url)
        elif usage.upper() == 'CF' or usage.upper() == 'CLOUDFLARE':
            await check_cloudflare(ctx, url)
        elif usage.upper() == 'HTTP':
            await check_http_security(ctx, url)
        elif usage.upper() == 'DOMAIN':
            await find_website(ctx, url)
        elif usage.upper() == 'DIRECTORIES' or usage.upper() == 'DIRT':
            await check_website_directories(ctx, url)
        elif usage.upper() == 'HELP':
            embed_description = (
                "**SSL**: Checks and Sends Info for the websites SSL certificate; Issuer, Time made / expiry, Serial number, Fingerprint, ASN1 and NIST curves\n"
                "**DNS**: Lists the Domain Name and any and all Connected IPs\n"
                "**STATUS**: Checks if the Server is Online\n"
                "**BLOCKED**: Shows Blocked DNS providers\n"
                "**HSTS**: Checks if the Host has HSTS Enabled\n"
                "**TRACEROUTE**: Preforms a Traceroute on the Server\n"
                "**SCRAPE / PROXYS**: Scrapes Proxies From a Given Site\n"
                "**SUBDOMAINS**: Lists Found Subdomains\n"
                "**DOMAINS**: Lists the Domain the Site is Under\n"
                "**CF / CLOUDFLARE**: Checks if the Server uses CloudFlare\n"
                "**HTTP**: Checks what HTTP Response Headers are set up\n"
                "**DRECTORIES / DIRT**: Searches for Accessable Directories and sends them if found\n"
            )

            embed = discord.Embed(
                title="Website Help",
                description=embed_description,
                color=0xff0000
            )

            embed.set_footer(text=GLOBAL_FOOTER)
            embed.set_image(url=GIF_URL)

            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=discord.Embed(description='Invalid usage. Please use one of: SSL, DNS, STATUS, BLOCKED, HSTS, TRACEROUTE, SCRAPE, PROXYS, SUBDOMAINS, DOMAINS, CF, CLOUDFLARE, HTTP, DIRECTORIES, DIRT, or HELP', color=0xff0000))


async def setup(bot):
    await bot.add_cog(Website(bot))
