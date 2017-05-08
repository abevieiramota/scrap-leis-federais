# -*- coding: utf-8 -*-
# biblioteca para requisição http
import requests
# biblioteca para parse do HTML retornado
from bs4 import BeautifulSoup
# biblioteca de expressão regular
import re
# biblioteca utilizada para construir as urls absolutas a partir das relativas
from urllib.parse import urljoin
import logging

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger("ScrapLeis")

REQUEST_HEADER = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

# TODO: formatar para tornar mais claro
RN_RE = re.compile(r"[\n\r\t\xa0]+")

TITULO_RE = r"(?P<titulo>TÍTULO\s+[IVX]+)"
ARTIGO_RE = r"(?P<artigo>Art.\s+\d+)"
PARAGRAFO_RE = r"(?P<paragrafo>(§\s+\d+|Parágrafo\ único))"
INCISO_RE = r"(?P<inciso>[IXV]+\ \-|[a-z](?=\)))"

ELEMENTOS_RE = [TITULO_RE,
                ARTIGO_RE,
                PARAGRAFO_RE,
                INCISO_RE]

TAG_RE = re.compile(r"^({})".format("|".join(ELEMENTOS_RE)), re.IGNORECASE)

DECRETO_LEI_RE = r"(?P<decreto>Decreto[\-\s]+lei\s+n\s*º\s+(?P<decreto_id>[\d\.]+(\-\w+)?),(\s+de)?\s+(\d{1,2}\.\d{1,2}\.)?\d{4})"
LEI_RE = r"(?P<lei>Lei\s+nº\s+(?P<lei_id>[\d\.]+),(\s+de)?\s+(\d{1,2}\.\d{1,2}\.)?\d{4})"
VIGENCIA_RE = r"(?P<vigencia>Vigência)"

TIPOS_LINKS_RE = [DECRETO_LEI_RE,
                  LEI_RE,
                  VIGENCIA_RE]

TIPO_LINK_RE = re.compile(r"({})".format("|".join(TIPOS_LINKS_RE)), re.IGNORECASE)

URL = "http://www.planalto.gov.br/ccivil_03/decreto-lei/Del5452.htm"

def download_html(url):
    
    r = requests.get(url, headers=REQUEST_HEADER)
    
    return r.text

def parse_html(html):
    
    return BeautifulSoup(html, "lxml")

def extrair_ps(parsed):
    
    return parsed.select("body p")

def limpar_texto(texto):
    
    return RN_RE.sub(" ", texto).strip()

def qual_grupo(regex, texto):
    
    elementos_match = regex.search(texto)
    
    if not elementos_match:
        
        return None, None
    
    matched_groups = {k:v for k,v in elementos_match.groupdict().items()\
                  if v is not None}
    
    if(len(matched_groups) > 2):
        
        logger.warning(texto)
        
        raise Exception("Elemento com mais de um match")
        
    grupo = [key for key in matched_groups.keys() if len(key.split("_")) == 1][0]
    grupo_id = None
    uncleaned_grupo_id = matched_groups.get("{}_id".format(grupo), None)
    if uncleaned_grupo_id:
        grupo_id = limpar_texto(uncleaned_grupo_id).replace(".", "")
    
    return grupo_id, grupo


def extrair_tag(p_atributo):
    
    p_atributo["tag_id"], p_atributo["tag"] = qual_grupo(TAG_RE, p_atributo["cleaned_texto"])


def extrair_links_alteracao(p_atributo, urlbase):
    
    anchors = p_atributo["p"].find_all("a", href=True)
    
    p_atributo["links"] = []
    
    for anchor in anchors:
        
        anchor_texto = limpar_texto(anchor.text)
        
        tipo_link_id, tipo_link = qual_grupo(TIPO_LINK_RE, anchor_texto)
        
        link = {"texto": anchor_texto,
                "href": urljoin(urlbase, anchor["href"]),
                "tipo": tipo_link,
                "tipo_id": tipo_link_id}
        
        p_atributo["links"].append(link)
        
        
def extrair_is_old(p_atributo):
    
    tem_strike = p_atributo["p"].find("strike")
    
    p_atributo["is_old"] = True if tem_strike else False
        

def extrair_atributos(ps):
    
    ps_atributos = []
    for p in ps:
        
        p_atributo = {"p": p,
                      "cleaned_texto": limpar_texto(p.text)}
        
        extrair_tag(p_atributo)
        extrair_links_alteracao(p_atributo, URL)
        extrair_is_old(p_atributo)
        
        ps_atributos.append(p_atributo)
        
    return ps_atributos

def do_all():
    
    html = download_html(URL)
    parsed_html = parse_html(html)
    ps = extrair_ps(parsed_html)
    
    return extrair_atributos(ps)

if __name__ == "__main__":
    
    html = download_html(URL)
    parsed_html = parse_html(html)
    ps = extrair_ps(parsed_html)
    tagged_ps = extrair_atributos(ps)
