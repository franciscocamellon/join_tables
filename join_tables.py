# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JoinTable
                                 A QGIS plugin
 Perform joins between spatial and non spatial tables
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-02-09
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Francisco Camello N
        email                : franciscocamellon@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os.path
import re

from PyQt5.QtCore import QSettings, QTranslator, qVersion
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtWidgets import QAction, QWidget, QMessageBox
from qgis.core import QgsVectorLayerJoinInfo, QgsProject, QgsPalLayerSettings, \
    QgsTextFormat, QgsPropertyCollection, QgsUnitTypes, QgsVectorLayerSimpleLabeling, QgsProperty
from qgis.utils import *

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .join_tables_dialog import JoinTableDialog



class JoinTable:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'JoinTable_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Join Tables')
        self.toolbar = self.iface.addToolBar(u'&Join Tables')
        self.toolbar.setObjectName(u'&Join Tables')
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        # --variables
        self.root = QgsProject.instance().layerTreeRoot()
        self.layers_tree = self.root.findLayers()


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('JoinTable', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        """
        # Check if the menu exists and get it
        self.menu = self.iface.mainWindow().findChild(QMenu, '&My tools')

        # If the menu does not exist, create it!
        if not self.menu:
            self.menu = QMenu('&My tools', self.iface.mainWindow().menuBar())
            self.menu.setObjectName('&My tools')
            actions = self.iface.mainWindow().menuBar().actions()
            lastAction = actions[-1]
            self.iface.mainWindow().menuBar().insertMenu(lastAction, self.menu)

        # Finally, add your action to the menu
        self.menu.addAction(self.action)
        """

        icon_path = ':/plugins/join_tables/icons/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Join'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Join Tables'),
                action)
            self.iface.removeToolBarIcon(action)

    def lyrDict(self):
        g_dict = {}
        t_dict = {}
        i = 0
        for layer_tree in self.layers_tree:
            layer = layer_tree.layer()

            if layer.type() == 0:
                layer_type = layer.geometryType()
                layer_name = layer.name()
                ids = self.root.findLayerIds()

                if layer_type == 0 or layer_type == 1:
                    g = layer_name
                    gids = ids[i]
                    g_dict[gids] = g_dict.setdefault(gids, g)
                elif layer_type == 4:
                    t = layer_name
                    tids = ids[i]
                    t_dict[tids] = t_dict.setdefault(tids, t)
                i += 1
        return g_dict, t_dict

    def lyrPair(self):
        g_dict, t_dict = self.lyrDict()
        d = {}
        f = {}
        for k, v in g_dict.items():
            for c, e in t_dict.items():
                if g_dict[k] == t_dict[c]:
                    d[k] = d.setdefault(k, c)
                    f[v] = f.setdefault(v, e)
        return d, f

    def removeJoinTables(self):  # for use in future in test for previous joins
        d, f = self.lyrPair()
        for k, v in d.items():
            target = QgsProject.instance().mapLayer(k)
            layerToJoin = QgsProject.instance().mapLayer(v)
            target.removeJoin(layerToJoin.id())
            target.triggerRepaint()

    def joinTables(self):
        d, f = self.lyrPair()
        for k, v in d.items():
            target = QgsProject.instance().mapLayer(k)
            layerToJoin = QgsProject.instance().mapLayer(v)
            """  # tests for previous joined layers - under research
            i = QgsProject.instance().mapLayers().values()
            for layer in i:
                fh_lyr = layer
                joinsInfo = fh_lyr.vectorJoins()
                
                if joinsInfo != 0:
                    QMessageBox.critical(iface.mainWindow(), "Error",
                                        "Previously Joins already exists! Please remove joins and try again.")
                    break  # ask for remove previous joins. use removeJoinTables()
                else:
            """
            # target.removeJoin(layerToJoin.id())
            fieldToJoin = QgsProject.instance()
            symb = QgsVectorLayerJoinInfo()
            symb.setJoinFieldName('id_feature')
            symb.setTargetFieldName('id')
            symb.setJoinLayerId(layerToJoin.id())
            symb.setUsingMemoryCache(True)
            symb.setEditable(True)
            symb.setDynamicFormEnabled(True)
            symb.setUpsertOnEdit(True)
            symb.setPrefix('')
            symb.setJoinFieldNamesSubset(['ocultar', 'legenda', 'tamanhotxt', 'justtxt', 'orient_txt', 'orient_simb',
                                          'offset_txt', 'offset_simb', 'prioridade', 'offset_txt_x', 'offset_txt_y'])
            symb.setJoinLayer(layerToJoin)
            target.addJoin(symb)
            layerToJoin.startEditing()
            target.triggerRepaint()

    def setFieldsCollection(self):
        fieldsColl = {
            0: 'tamanhotxt',
            21: 'estilo',
            27: 'casetxt',
            28: 'flspacing',
            29: 'fwspacing',
            33: 'justtxt',
            77: 'offset_quad',
            78: 'offset_txt',
            87: 'prioridade',
            96: 'orient_txt',
            9: 'offset_txt_x',
            10: 'offset_txt_y'
        }
        return fieldsColl

    def setArialDict(self):
        arialDict = {
            1: "loc_nome_local_p",
            2: "pto_area_est_med_fenom_a",
            3: "pto_pto_controle_p",
            4: "pto_pto_est_med_fenomenos_p",
            5: "pto_pto_geod_topo_controle_p",
            6: "pto_pto_ref_geod_topo_p",
            7: "rel_alter_fisiog_antropica_a",
            8: "rel_alter_fisiog_antropica_l",
            9: "rel_elemento_fisiog_natural_a",
            10: "rel_elemento_fisiog_natural_l",
            11: "rel_elemento_fisiog_natural_p",
            12: "rel_pico_p",
            13: "rel_terreno_exposto_a"
        }
        return arialDict

    def setSsnrDict(self):
        ssnrDict = {
            1: "adm_edif_pub_civil_a",
            2: "adm_edif_pub_civil_p",
            3: "adm_edif_pub_militar_a",
            4: "adm_edif_pub_militar_p",
            5: "adm_posto_fiscal_a",
            6: "adm_posto_fiscal_p",
            7: "adm_posto_pol_rod_a",
            8: "adm_posto_pol_rod_p",
            9: "asb_area_abast_agua_a",
            10: "asb_area_saneamento_a",
            11: "asb_cemiterio_a",
            12: "asb_cemiterio_p",
            13: "asb_dep_abast_agua_a",
            14: "asb_dep_abast_agua_p",
            15: "asb_dep_saneamento_a",
            16: "asb_dep_saneamento_p",
            17: "asb_edif_abast_agua_a",
            18: "asb_edif_abast_agua_p",
            19: "asb_edif_saneamento_a",
            20: "asb_edif_saneamento_p",
            21: "eco_area_agrop_ext_veg_pesca_a",
            22: "eco_area_comerc_serv_a",
            23: "eco_area_ext_mineral_a",
            24: "eco_area_industrial_a",
            25: "eco_deposito_geral_a",
            26: "eco_deposito_geral_p",
            27: "eco_edif_agrop_ext_veg_pesca_a",
            28: "eco_edif_agrop_ext_veg_pesca_p",
            29: "eco_edif_comerc_serv_a",
            30: "eco_edif_comerc_serv_p",
            31: "eco_edif_ext_mineral_a",
            32: "eco_edif_ext_mineral_p",
            33: "eco_edif_industrial_a",
            34: "eco_edif_industrial_p",
            35: "eco_equip_agropec_a",
            36: "eco_equip_agropec_l",
            37: "eco_equip_agropec_p",
            38: "eco_ext_mineral_a",
            39: "eco_ext_mineral_p",
            40: "eco_plataforma_a",
            41: "eco_plataforma_p",
            42: "edu_area_ensino_a",
            43: "edu_area_lazer_a",
            44: "edu_area_religiosa_a",
            45: "edu_area_ruinas_a",
            46: "edu_arquibancada_a",
            47: "edu_arquibancada_p",
            48: "edu_campo_quadra_a",
            49: "edu_campo_quadra_p",
            50: "edu_coreto_tribuna_a",
            51: "edu_coreto_tribuna_p",
            52: "edu_edif_const_lazer_a",
            53: "edu_edif_const_lazer_p",
            54: "edu_edif_const_turistica_a",
            55: "edu_edif_const_turistica_p",
            56: "edu_edif_ensino_a",
            57: "edu_edif_ensino_p",
            58: "edu_edif_religiosa_a",
            59: "edu_edif_religiosa_p",
            60: "edu_piscina_a",
            61: "edu_pista_competicao_l",
            62: "edu_ruina_a",
            63: "edu_ruina_p",
            64: "enc_antena_comunic_p",
            65: "enc_area_comunicacao_a",
            66: "enc_area_energia_eletrica_a",
            67: "enc_edif_comunic_a",
            68: "enc_edif_comunic_p",
            69: "enc_edif_energia_a",
            70: "enc_edif_energia_p",
            71: "enc_est_gerad_energia_eletr_a",
            72: "enc_est_gerad_energia_eletr_l",
            73: "enc_est_gerad_energia_eletr_p",
            74: "enc_grupo_transformadores_a",
            75: "enc_grupo_transformadores_p",
            76: "enc_hidreletrica_a",
            77: "enc_hidreletrica_l",
            78: "enc_hidreletrica_p",
            79: "enc_ponto_trecho_energia_p",
            80: "enc_termeletrica_a",
            81: "enc_termeletrica_p",
            82: "enc_torre_comunic_p",
            83: "enc_torre_energia_p",
            84: "enc_trecho_comunic_l",
            85: "enc_trecho_energia_l",
            86: "enc_zona_linhas_energia_com_a",
            87: "hid_natureza_fundo_a",
            88: "hid_natureza_fundo_l",
            89: "hid_natureza_fundo_p",
            90: "hid_recife_a",
            91: "hid_recife_l",
            92: "hid_recife_p",
            93: "hid_rocha_em_agua_a",
            94: "hid_rocha_em_agua_p",
            95: "lim_area_especial_a",
            96: "lim_area_especial_p",
            97: "lim_marco_de_limite_p",
            98: "loc_area_edificada_a",
            99: "loc_edif_habitacional_a",
            100: "loc_edif_habitacional_p",
            101: "loc_edificacao_a",
            102: "loc_edificacao_p",
            103: "pto_edif_constr_est_med_fen_a",
            104: "pto_edif_constr_est_med_fen_p",
            105: "rel_dolina_a",
            106: "rel_dolina_p",
            107: "rel_duna_a",
            108: "rel_duna_p",
            109: "rel_gruta_caverna_p",
            110: "rel_rocha_a",
            111: "rel_rocha_p",
            112: "sau_area_saude_a",
            113: "sau_area_servico_social_a",
            114: "sau_edif_saude_a",
            115: "sau_edif_saude_p",
            116: "sau_edif_servico_social_a",
            117: "sau_edif_servico_social_p",
            118: "tra_area_duto_a",
            119: "tra_area_estrut_transporte_a",
            120: "tra_arruamento_l",
            121: "tra_atracadouro_a",
            122: "tra_atracadouro_l",
            123: "tra_atracadouro_p",
            124: "tra_caminho_aereo_l",
            125: "tra_ciclovia_l",
            126: "tra_condutor_hidrico_l",
            127: "tra_cremalheira_l",
            128: "tra_cremalheira_p",
            129: "tra_eclusa_a",
            130: "tra_eclusa_l",
            131: "tra_eclusa_p",
            132: "tra_edif_constr_aeroportuaria_a",
            133: "tra_edif_constr_aeroportuaria_p",
            134: "tra_edif_constr_portuaria_a",
            135: "tra_edif_constr_portuaria_p",
            136: "tra_edif_metro_ferroviaria_a",
            137: "tra_edif_metro_ferroviaria_p",
            138: "tra_edif_rodoviaria_a",
            139: "tra_edif_rodoviaria_p",
            140: "tra_entroncamento_p",
            141: "tra_faixa_seguranca_a",
            142: "tra_fundeadouro_a",
            143: "tra_fundeadouro_l",
            144: "tra_fundeadouro_p",
            145: "tra_funicular_l",
            146: "tra_funicular_p",
            147: "tra_galeria_bueiro_l",
            148: "tra_galeria_bueiro_p",
            149: "tra_girador_ferroviario_p",
            150: "tra_identific_trecho_rod_p",
            151: "tra_local_critico_a",
            152: "tra_local_critico_l",
            153: "tra_local_critico_p",
            154: "tra_obstaculo_navegacao_a",
            155: "tra_obstaculo_navegacao_l",
            156: "tra_obstaculo_navegacao_p",
            157: "tra_passag_elevada_viaduto_l",
            158: "tra_passag_elevada_viaduto_p",
            159: "tra_passagem_nivel_p",
            160: "tra_patio_a",
            161: "tra_patio_p",
            162: "tra_pista_ponto_pouso_a",
            163: "tra_pista_ponto_pouso_l",
            164: "tra_pista_ponto_pouso_p",
            165: "tra_ponte_l",
            166: "tra_ponte_p",
            167: "tra_ponto_duto_p",
            168: "tra_ponto_ferroviario_p",
            169: "tra_ponto_hidroviario_p",
            170: "tra_ponto_rodoviario_p",
            171: "tra_posto_combustivel_a",
            172: "tra_posto_combustivel_p",
            173: "tra_sinalizacao_p",
            174: "tra_travessia_l",
            175: "tra_travessia_p",
            176: "tra_travessia_pedestre_l",
            177: "tra_travessia_pedestre_p",
            178: "tra_trecho_duto_l",
            179: "tra_trecho_ferroviario_l",
            180: "tra_trecho_hidroviario_l",
            181: "tra_trecho_rodoviario_l",
            182: "tra_trilha_picada_l",
            183: "tra_tunel_l",
            184: "tra_tunel_p",
            185: "veg_brejo_pantano_a",
            186: "veg_caatinga_a",
            187: "veg_campinarana_a",
            188: "veg_campo_a",
            189: "veg_cerrado_cerradao_a",
            190: "veg_estepe_a",
            191: "veg_floresta_a",
            192: "veg_macega_chavascal_a",
            193: "veg_mangue_a",
            194: "veg_veg_area_contato_a",
            195: "veg_veg_cultivada_a",
            196: "veg_veg_restinga_a",
            197: "veg_vegetacao_a",
        }
        return ssnrDict

    def setSwiDict(self):
        swiDict = {
            1: "hid_area_umida_a",
            2: "hid_bacia_hidrografica_a",
            3: "hid_banco_areia_a",
            4: "hid_banco_areia_l",
            5: "hid_barragem_a",
            6: "hid_barragem_l",
            7: "hid_barragem_p",
            8: "hid_comporta_l",
            9: "hid_comporta_p",
            10: "hid_confluencia_p",
            11: "hid_corredeira_a",
            12: "hid_corredeira_l",
            13: "hid_corredeira_p",
            14: "hid_fonte_dagua_p",
            15: "hid_foz_maritima_a",
            16: "hid_foz_maritima_l",
            17: "hid_foz_maritima_p",
            18: "hid_ilha_a",
            19: "hid_ilha_l",
            20: "hid_ilha_p",
            21: "hid_limite_massa_dagua_l",
            22: "hid_massa_dagua_a",
            23: "hid_ponto_drenagem_p",
            24: "hid_ponto_inicio_drenagem_p",
            25: "hid_quebramar_molhe_a",
            26: "hid_quebramar_molhe_l",
            27: "hid_queda_dagua_a",
            28: "hid_queda_dagua_l",
            29: "hid_queda_dagua_p",
            30: "hid_reservatorio_hidrico_a",
            31: "hid_sumidouro_vertedouro_p",
            32: "hid_terreno_suj_inundacao_a",
            33: "hid_trecho_drenagem_l",
            34: "hid_trecho_massa_dagua_a",
            35: "rel_curva_batimetrica_l",
            36: "rel_curva_nivel_l",
            37: "rel_ponto_cotado_altimetrico_p",
            38: "rel_ponto_cotado_batimetrico_p",
        }
        return swiDict

    def setTimesDict(self):
        timesDict = {
            1: "adm_area_pub_civil_a",
            2: "adm_area_pub_militar_a",
            3: "lim_area_de_litigio_a",
            4: "lim_area_desenv_controle_a",
            5: "lim_area_desenv_controle_p",
            6: "lim_area_particular_a",
            7: "lim_area_politico_adm_a",
            8: "lim_area_uso_comunitario_a",
            9: "lim_area_uso_comunitario_p",
            10: "lim_bairro_a",
            11: "lim_delimitacao_fisica_l",
            12: "lim_distrito_a",
            13: "lim_limite_area_especial_l",
            14: "lim_limite_intra_munic_adm_l",
            15: "lim_limite_operacional_l",
            16: "lim_limite_particular_l",
            17: "lim_limite_politico_adm_l",
            18: "lim_linha_de_limite_l",
            19: "lim_municipio_a",
            20: "lim_outras_unid_protegidas_a",
            21: "lim_outras_unid_protegidas_p",
            22: "lim_outros_limites_oficiais_l",
            23: "lim_pais_a",
            24: "lim_regiao_administrativa_a",
            25: "lim_sub_distrito_a",
            26: "lim_terra_indigena_a",
            27: "lim_terra_indigena_p",
            28: "lim_terra_publica_a",
            29: "lim_terra_publica_p",
            30: "lim_unidade_conserv_nao_snuc_a",
            31: "lim_unidade_conserv_nao_snuc_p",
            32: "lim_unidade_federacao_a",
            33: "lim_unidade_protecao_integral_a",
            34: "lim_unidade_protecao_integral_p",
            35: "lim_unidade_uso_sustentavel_a",
            36: "lim_unidade_uso_sustentavel_p",
            37: "loc_aglom_rural_de_ext_urbana_p",
            38: "loc_aglomerado_rural_isolado_p",
            39: "loc_aglomerado_rural_p",
            40: "loc_area_habitacional_a",
            41: "loc_area_urbana_isolada_a",
            42: "loc_capital_p",
            43: "loc_cidade_p",
            44: "loc_hab_indigena_a",
            45: "loc_hab_indigena_p",
            46: "loc_localidade_p",
            47: "loc_vila_p",
        }
        return timesDict

    def setCollectionSettings(self):
        lyrids, lyrnames = self.lyrPair()
        coll = self.setFieldsCollection()
        arial = self.setArialDict()
        ssnr = self.setSsnrDict()
        swi = self.setSwiDict()
        times = self.setTimesDict()

        for names in lyrnames.values():
            lyr = QgsProject.instance().mapLayersByName(names)[0]
            iface.setActiveLayer(lyr)
            pc = QgsPropertyCollection('qpc')
            lyr_settings = QgsPalLayerSettings()
            txt_format = QgsTextFormat()
            txt_format.setSizeUnit(QgsUnitTypes.RenderPoints)

            for nColl, fColl in coll.items():
                x = QgsProperty()
                x.setField(fColl)
                pc.setProperty(nColl, x)
                pc.setProperty(31, '/')
                pc.setProperty(32, 0.8)

                if names in arial.values():
                    txt_format.setFont(QFont("Arial"))
                    txt_format.setColor(QColor(0, 0, 0))
                elif names in ssnr.values():
                    txt_format.setFont(QFont("Xerox Sans Serif Narrow"))
                    txt_format.setColor(QColor(0, 0, 0))
                elif names in swi.values():
                    txt_format.setFont(QFont("Xerox Serif Wide"))
                    if re.search(r"\Bcotado", names):
                        txt_format.setColor(QColor(140, 58, 61))
                    elif re.search(r"\Bcurva", names):
                        txt_format.setColor(QColor(140, 58, 61))
                    else:
                        txt_format.setColor(QColor(0, 119, 189))
                elif names in times.values():
                    txt_format.setFont(QFont("Times New Roman"))
                    txt_format.setColor(QColor(0, 0, 0))
                pass

            lyr_settings.setFormat(txt_format)
            lyr_settings.setDataDefinedProperties(pc)
            lyr_settings.enabled = True
            if names == "rel_ponto_cotado_altimetrico_p":
                lyr_settings.fieldName = "cota"
            else:
                lyr_settings.fieldName = "legenda"
            lyr_settings = QgsVectorLayerSimpleLabeling(lyr_settings)
            lyr.setLabelsEnabled(True)
            lyr.setLabeling(lyr_settings)
            lyr.triggerRepaint()

    def run(self):
        """Run method that performs all the real work"""
        self.joinTables()
        self.setCollectionSettings()
        iface.messageBar().pushMessage("Success", "All settings done!", level=0, duration=3)