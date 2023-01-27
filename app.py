import asyncio
import aiohttp
import os
from bs4 import BeautifulSoup
from flask import Flask, render_template


async def get_informacao_fii(sessao, codigo_fii):
    url = f'https://fiis.com.br/{codigo_fii}'
    async with sessao.get(url) as resp_fiis:
        dados_fii = {}
        dados_fii['codigo'] = codigo_fii.upper()
        dados_fii['url'] = url
        dados_fii['status'] = resp_fiis.status

        html = BeautifulSoup(await resp_fiis.read(), 'html.parser')

        try:
            dados_fii['patrimonial'] = html.find_all(class_='indicators__box')[6].b.contents[0]                     # caminho atualizado
        except:
            dados_fii['patrimonial'] = None

        try:
            dados_fii['cotacao'] = html.find(class_='item quotation').find(class_='value').contents[0]              # caminho OK
        except:
            dados_fii['cotacao'] = None

        dados_fii['rendimento'] = []
        dados_fii['data_pagamento'] = []
        dados_fii['data_base'] = []

        try:
            for linha in html.find(class_="yieldChart__dados").find_all(class_='yieldChart__table__bloco')[1:]:     # caminho atualizado
                coluna = list(linha.stripped_strings)
                dados_fii['rendimento'].append(coluna[4].split()[1])
                dados_fii['data_pagamento'].append(coluna[1])
                dados_fii['data_base'].append(coluna[0])
        except:
            dados_fii['rendimento'].append(None)
            dados_fii['data_pagamento'].append(None)
            dados_fii['data_base'].append(None)

        try:
            atualizacoes = html.find(id='news--wrapper').find_all('a')                                              # TODO
            emissao_cotas = [item.get_text(strip=True).find('Cotas') for item in atualizacoes]
            dados_fii['cotas'] = bool(sum([x for x in emissao_cotas if x != -1]))
        except:
            dados_fii['cotas'] = None

        return dados_fii


async def get_lista_fiis():
    async with aiohttp.ClientSession() as sessao:
        lista_fiis = []
        async with sessao.get(os.environ.get('URL_FIREBASE')) as resp_firebase:
            try:
                lista_fiis = await resp_firebase.json()
            except:
                lista_fiis = ['error']
        
        tasks = [get_informacao_fii(sessao, fii) for fii in lista_fiis]
        dados_lista_fiis = await asyncio.gather(*tasks)
        
        return dados_lista_fiis


app = Flask(__name__)


@app.route('/')
async def tabela_fiis():
    dados_lista = await get_lista_fiis()
    dados = sorted(dados_lista, key=lambda x: x['codigo'])
    return render_template('table.html', dados=dados)


if __name__ == '__main__':
    app.run()
