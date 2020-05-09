from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import hashlib
import base64
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import urllib.parse

SANAL_POS = {
    'customer_id': '400235',
    'merchant_id': '496',
    'username': 'apitest',
    'password': 'api123',
    'ok_url': 'http://127.0.0.1:8000/ok-url/',
    'fail_url': 'http://127.0.0.1:8000/fail-url/',
    'kart_onay_url': 'https://boatest.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelPayGate',
    'odeme_onay_url': 'https://boatest.kuveytturk.com.tr/boa.virtualpos.services/Home/ThreeDModelProvisionGate',
} # DEBUG == True şeklinde kontrol yaparak prod'a göre conf yapabilirsiniz


def index(request):
    return render(request, 'index.html')


@require_http_methods(['POST'])
def odeme(request):
    name = request.POST.get('name')
    expiry = request.POST.get('expiry').split('/')
    year = expiry[1].strip()
    month = expiry[0].strip()
    number = request.POST.get('number').replace(' ', '')
    cvc = request.POST.get('cvc')
    merchant_order_id = 'web-odeme'
    tutar = 5 * 100
    hashed_password = base64.b64encode(hashlib.sha1(f"{SANAL_POS['password']}".encode('ISO-8859-9')).digest()).decode()
    hashed_data = base64.b64encode(hashlib.sha1(
        f"{SANAL_POS['merchant_id']}{merchant_order_id}{tutar}{SANAL_POS['ok_url']}{SANAL_POS['fail_url']}{SANAL_POS['username']}{hashed_password}".encode(
            'ISO-8859-9')).digest()).decode()
    data = f"""
        <KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchemainstance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <APIVersion>1.0.0</APIVersion>
    <OkUrl>{str(SANAL_POS["ok_url"])}</OkUrl>
    <FailUrl>{str(SANAL_POS["fail_url"])}</FailUrl>
    <HashData>{hashed_data}</HashData>
    <MerchantId>{int(SANAL_POS['merchant_id'])}</MerchantId>
    <CustomerId>{int(SANAL_POS['customer_id'])}</CustomerId>
    <UserName>{str(SANAL_POS['username'])}</UserName>
    <CardNumber>{str(number)}</CardNumber>
    <CardExpireDateYear>{str(year)}</CardExpireDateYear>
    <CardExpireDateMonth>{str(month)}</CardExpireDateMonth>
    <CardCVV2>{str(cvc)}</CardCVV2>
    <CardHolderName>{str(name)}</CardHolderName>
    <CardType>Troy</CardType>
    <TransactionType>Sale</TransactionType>
    <InstallmentCount>{int('0')}</InstallmentCount>
    <Amount>{int(tutar)}</Amount>
    <DisplayAmount>{int(tutar)}</DisplayAmount>
    <CurrencyCode>{str('0949')}</CurrencyCode>
    <MerchantOrderId>{str(merchant_order_id)}</MerchantOrderId>
    <TransactionSecurity>{int('3')}</TransactionSecurity>
    </KuveytTurkVPosMessage>
    """
    headers = {'Content-Type': 'application/xml'}
    r = requests.post(SANAL_POS['kart_onay_url'], data=data.encode('ISO-8859-9'), headers=headers)
    return HttpResponse(r)


@require_http_methods(['POST'])
@csrf_exempt
def ok_url(request):
    gelen = request.POST.get('AuthenticationResponse')
    data = urllib.parse.unquote(gelen)
    merchant_order_id_start = data.find('<MerchantOrderId>')
    merchant_order_id_stop = data.find('</MerchantOrderId>')
    merchant_order_id = data[merchant_order_id_start + 17:merchant_order_id_stop]
    amount_start = data.find('<Amount>')
    amount_end = data.find('</Amount>')
    amount = data[amount_start + 8:amount_end]
    md_start = data.find('<MD>')
    md_end = data.find('</MD>')
    md = data[md_start + 4:md_end]
    hashed_password = base64.b64encode(
        hashlib.sha1(SANAL_POS["password"].encode('ISO-8859-9')).digest()).decode()
    hashed_data = base64.b64encode(hashlib.sha1(
        f'{SANAL_POS["merchant_id"]}{merchant_order_id}{amount}{SANAL_POS["username"]}{hashed_password}'.encode(
            "ISO-8859-9")).digest()).decode()
    xml = f"""
    <KuveytTurkVPosMessage xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <APIVersion>1.0.0</APIVersion>
    <HashData>{hashed_data}</HashData>
    <MerchantId>{int(SANAL_POS['merchant_id'])}</MerchantId>
    <CustomerId>{int(SANAL_POS['customer_id'])}</CustomerId>
    <UserName>{str(SANAL_POS['username'])}</UserName>
    <TransactionType>Sale</TransactionType>
    <InstallmentCount>0</InstallmentCount>
    <Amount>{amount}</Amount>
    <MerchantOrderId>{str(merchant_order_id)}</MerchantOrderId>
    <TransactionSecurity>3</TransactionSecurity>
    <KuveytTurkVPosAdditionalData>
    <AdditionalData>
    <Key>MD</Key>
    <Data>{md}</Data>
    </AdditionalData>
     </KuveytTurkVPosAdditionalData>
    </KuveytTurkVPosMessage>
    """
    headers = {'Content-Type': 'application/xml'}
    r = requests.post(SANAL_POS['odeme_onay_url'], data=xml.encode('ISO-8859-9'), headers=headers)
    return HttpResponse(r)


@require_http_methods(['POST'])
@csrf_exempt
def fail_url(request):
    pass
