# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'signs_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.2.4
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDockWidget, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget)

class Ui_SignsEditor(object):
    def setupUi(self, SignsEditor):
        if not SignsEditor.objectName():
            SignsEditor.setObjectName(u"SignsEditor")
        SignsEditor.resize(350, 495)
        self.verticalLayoutWidget = QWidget()
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(self.verticalLayoutWidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, -209, 316, 694))
        self.verticalLayout1 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout1.setObjectName(u"verticalLayout1")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayoutInside = QVBoxLayout()
        self.verticalLayoutInside.setObjectName(u"verticalLayoutInside")
        self.h_links = QHBoxLayout()
        self.h_links.setObjectName(u"h_links")
        self.mapillary_label = QLabel(self.scrollAreaWidgetContents)
        self.mapillary_label.setObjectName(u"mapillary_label")

        self.h_links.addWidget(self.mapillary_label)

        self.mapillarytype = QPushButton(self.scrollAreaWidgetContents)
        self.mapillarytype.setObjectName(u"mapillarytype")
        self.mapillarytype.setMaximumSize(QSize(55, 55))
        self.mapillarytype.setIconSize(QSize(50, 50))

        self.h_links.addWidget(self.mapillarytype)


        self.verticalLayoutInside.addLayout(self.h_links)

        self.not_a_sign = QCheckBox(self.scrollAreaWidgetContents)
        self.not_a_sign.setObjectName(u"not_a_sign")

        self.verticalLayoutInside.addWidget(self.not_a_sign)

        self.h_id = QHBoxLayout()
        self.h_id.setObjectName(u"h_id")
        self.id_label = QLabel(self.scrollAreaWidgetContents)
        self.id_label.setObjectName(u"id_label")
        self.id_label.setMaximumSize(QSize(180, 25))

        self.h_id.addWidget(self.id_label)

        self.sign_id = QLabel(self.scrollAreaWidgetContents)
        self.sign_id.setObjectName(u"sign_id")
        self.sign_id.setMaximumSize(QSize(200, 25))

        self.h_id.addWidget(self.sign_id)

        self.sign_id_edit = QLineEdit(self.scrollAreaWidgetContents)
        self.sign_id_edit.setObjectName(u"sign_id_edit")
        self.sign_id_edit.setMaximumSize(QSize(200, 25))

        self.h_id.addWidget(self.sign_id_edit)


        self.verticalLayoutInside.addLayout(self.h_id)

        self.mapillary_type_label = QLabel(self.scrollAreaWidgetContents)
        self.mapillary_type_label.setObjectName(u"mapillary_type_label")

        self.verticalLayoutInside.addWidget(self.mapillary_type_label)

        self.h_mapinfo = QHBoxLayout()
        self.h_mapinfo.setObjectName(u"h_mapinfo")
        self.mapillary_label1 = QLabel(self.scrollAreaWidgetContents)
        self.mapillary_label1.setObjectName(u"mapillary_label1")

        self.h_mapinfo.addWidget(self.mapillary_label1)

        self.code_text = QTextEdit(self.scrollAreaWidgetContents)
        self.code_text.setObjectName(u"code_text")
        self.code_text.setMaximumSize(QSize(50, 30))

        self.h_mapinfo.addWidget(self.code_text)

        self.brasiltype = QPushButton(self.scrollAreaWidgetContents)
        self.brasiltype.setObjectName(u"brasiltype")
        self.brasiltype.setMaximumSize(QSize(55, 55))
        icon = QIcon()
        icon.addFile(u"styles/symbols_br/A-2b.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.brasiltype.setIcon(icon)
        self.brasiltype.setIconSize(QSize(50, 50))

        self.h_mapinfo.addWidget(self.brasiltype)


        self.verticalLayoutInside.addLayout(self.h_mapinfo)

        self.h_face = QHBoxLayout()
        self.h_face.setObjectName(u"h_face")
        self.face_label = QLabel(self.scrollAreaWidgetContents)
        self.face_label.setObjectName(u"face_label")
        self.face_label.setMaximumSize(QSize(280, 25))

        self.h_face.addWidget(self.face_label)

        self.face = QLineEdit(self.scrollAreaWidgetContents)
        self.face.setObjectName(u"face")
        self.face.setMaximumSize(QSize(100, 25))

        self.h_face.addWidget(self.face)


        self.verticalLayoutInside.addLayout(self.h_face)

        self.hboxLayout = QHBoxLayout()
        self.hboxLayout.setObjectName(u"hboxLayout")
        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName(u"label")
        self.label.setMaximumSize(QSize(80, 25))

        self.hboxLayout.addWidget(self.label)

        self.text1 = QLineEdit(self.scrollAreaWidgetContents)
        self.text1.setObjectName(u"text1")
        self.text1.setMaximumSize(QSize(220, 25))

        self.hboxLayout.addWidget(self.text1)

        self.remember1 = QCheckBox(self.scrollAreaWidgetContents)
        self.remember1.setObjectName(u"remember1")
        self.remember1.setMaximumSize(QSize(20, 25))

        self.hboxLayout.addWidget(self.remember1)


        self.verticalLayoutInside.addLayout(self.hboxLayout)

        self.hboxLayout1 = QHBoxLayout()
        self.hboxLayout1.setObjectName(u"hboxLayout1")
        self.label1 = QLabel(self.scrollAreaWidgetContents)
        self.label1.setObjectName(u"label1")
        self.label1.setMaximumSize(QSize(80, 25))

        self.hboxLayout1.addWidget(self.label1)

        self.text2 = QLineEdit(self.scrollAreaWidgetContents)
        self.text2.setObjectName(u"text2")
        self.text2.setMaximumSize(QSize(220, 25))

        self.hboxLayout1.addWidget(self.text2)

        self.remember2 = QCheckBox(self.scrollAreaWidgetContents)
        self.remember2.setObjectName(u"remember2")
        self.remember2.setMaximumSize(QSize(20, 25))

        self.hboxLayout1.addWidget(self.remember2)


        self.verticalLayoutInside.addLayout(self.hboxLayout1)

        self.hboxLayout2 = QHBoxLayout()
        self.hboxLayout2.setObjectName(u"hboxLayout2")
        self.segment = QPushButton(self.scrollAreaWidgetContents)
        self.segment.setObjectName(u"segment")
        self.segment.setMaximumSize(QSize(80, 25))

        self.hboxLayout2.addWidget(self.segment)

        self.road_segment = QTextEdit(self.scrollAreaWidgetContents)
        self.road_segment.setObjectName(u"road_segment")
        self.road_segment.setMaximumSize(QSize(220, 50))

        self.hboxLayout2.addWidget(self.road_segment)


        self.verticalLayoutInside.addLayout(self.hboxLayout2)

        self.hboxLayout3 = QHBoxLayout()
        self.hboxLayout3.setObjectName(u"hboxLayout3")
        self.label2 = QLabel(self.scrollAreaWidgetContents)
        self.label2.setObjectName(u"label2")
        self.label2.setMaximumSize(QSize(80, 25))

        self.hboxLayout3.addWidget(self.label2)

        self.observations = QTextEdit(self.scrollAreaWidgetContents)
        self.observations.setObjectName(u"observations")
        self.observations.setMaximumSize(QSize(220, 50))

        self.hboxLayout3.addWidget(self.observations)


        self.verticalLayoutInside.addLayout(self.hboxLayout3)

        self.h_face1 = QHBoxLayout()
        self.h_face1.setObjectName(u"h_face1")
        self.correctly_identified = QCheckBox(self.scrollAreaWidgetContents)
        self.correctly_identified.setObjectName(u"correctly_identified")

        self.h_face1.addWidget(self.correctly_identified)


        self.verticalLayoutInside.addLayout(self.h_face1)

        self.h_suporte = QHBoxLayout()
        self.h_suporte.setObjectName(u"h_suporte")
        self.suporte_label = QLabel(self.scrollAreaWidgetContents)
        self.suporte_label.setObjectName(u"suporte_label")
        self.suporte_label.setMaximumSize(QSize(150, 25))

        self.h_suporte.addWidget(self.suporte_label)

        self.textsuporte = QLineEdit(self.scrollAreaWidgetContents)
        self.textsuporte.setObjectName(u"textsuporte")
        self.textsuporte.setMaximumSize(QSize(200, 25))

        self.h_suporte.addWidget(self.textsuporte)

        self.remembersuporte = QCheckBox(self.scrollAreaWidgetContents)
        self.remembersuporte.setObjectName(u"remembersuporte")
        self.remembersuporte.setMaximumSize(QSize(20, 25))

        self.h_suporte.addWidget(self.remembersuporte)


        self.verticalLayoutInside.addLayout(self.h_suporte)

        self.h_suporte1 = QHBoxLayout()
        self.h_suporte1.setObjectName(u"h_suporte1")
        self.composta = QCheckBox(self.scrollAreaWidgetContents)
        self.composta.setObjectName(u"composta")

        self.h_suporte1.addWidget(self.composta)

        self.compost_choose = QPushButton(self.scrollAreaWidgetContents)
        self.compost_choose.setObjectName(u"compost_choose")

        self.h_suporte1.addWidget(self.compost_choose)


        self.verticalLayoutInside.addLayout(self.h_suporte1)


        self.horizontalLayout.addLayout(self.verticalLayoutInside)


        self.verticalLayout1.addLayout(self.horizontalLayout)

        self.h_date = QVBoxLayout()
        self.h_date.setObjectName(u"h_date")
        self.first_seen = QLabel(self.scrollAreaWidgetContents)
        self.first_seen.setObjectName(u"first_seen")
        self.first_seen.setMaximumSize(QSize(240, 25))

        self.h_date.addWidget(self.first_seen)

        self.last_seen = QLabel(self.scrollAreaWidgetContents)
        self.last_seen.setObjectName(u"last_seen")
        self.last_seen.setMaximumSize(QSize(240, 25))

        self.h_date.addWidget(self.last_seen)


        self.verticalLayout1.addLayout(self.h_date)

        self.vertbuttonLayout = QVBoxLayout()
        self.vertbuttonLayout.setObjectName(u"vertbuttonLayout")
        self.pushButton_save = QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_save.setObjectName(u"pushButton_save")
        self.pushButton_save.setMaximumSize(QSize(250, 16777215))

        self.vertbuttonLayout.addWidget(self.pushButton_save)

        self.pushButton_next = QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_next.setObjectName(u"pushButton_next")
        self.pushButton_next.setMaximumSize(QSize(250, 16777215))

        self.vertbuttonLayout.addWidget(self.pushButton_next)

        self.pushButton_next_no_save = QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_next_no_save.setObjectName(u"pushButton_next_no_save")
        self.pushButton_next_no_save.setMaximumSize(QSize(250, 16777215))

        self.vertbuttonLayout.addWidget(self.pushButton_next_no_save)


        self.verticalLayout1.addLayout(self.vertbuttonLayout)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)

        SignsEditor.setWidget(self.verticalLayoutWidget)

        self.retranslateUi(SignsEditor)

        QMetaObject.connectSlotsByName(SignsEditor)
    # setupUi

    def retranslateUi(self, SignsEditor):
        SignsEditor.setWindowTitle(QCoreApplication.translate("SignsEditor", u"Signs Editor", None))
        self.mapillary_label.setText(QCoreApplication.translate("SignsEditor", u"Mapillary type", None))
        self.mapillarytype.setText("")
        self.not_a_sign.setText(QCoreApplication.translate("SignsEditor", u"Not a Sign", None))
        self.id_label.setText(QCoreApplication.translate("SignsEditor", u"Sign ID", None))
        self.mapillary_type_label.setText(QCoreApplication.translate("SignsEditor", u"type", None))
        self.mapillary_label1.setText(QCoreApplication.translate("SignsEditor", u"Local type ", None))
        self.brasiltype.setText("")
        self.face_label.setText(QCoreApplication.translate("SignsEditor", u"Face value", None))
        self.label.setText(QCoreApplication.translate("SignsEditor", u"Text 1", None))
        self.label1.setText(QCoreApplication.translate("SignsEditor", u"Text 2", None))
        self.segment.setText(QCoreApplication.translate("SignsEditor", u"Segment", None))
        self.label2.setText(QCoreApplication.translate("SignsEditor", u"Observations", None))
        self.correctly_identified.setText(QCoreApplication.translate("SignsEditor", u"Identified correctly", None))
        self.suporte_label.setText(QCoreApplication.translate("SignsEditor", u"Support", None))
        self.composta.setText(QCoreApplication.translate("SignsEditor", u"Composite", None))
        self.compost_choose.setText(QCoreApplication.translate("SignsEditor", u"Select", None))
        self.pushButton_save.setText(QCoreApplication.translate("SignsEditor", u"Save", None))
        self.pushButton_next.setText(QCoreApplication.translate("SignsEditor", u"Save And Go", None))
        self.pushButton_next_no_save.setText(QCoreApplication.translate("SignsEditor", u"Next", None))
    # retranslateUi

