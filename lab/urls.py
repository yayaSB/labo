from django.urls import path

from . import views

urlpatterns = [
    path("", views.role_redirect, name="role_redirect"),
    path("profil/", views.profile_settings, name="profile_settings"),
    path("dashboard/etudiant/", views.DashboardEtudiantView.as_view(), name="dashboard_etudiant"),
    path(
        "dashboard/enseignant/",
        views.DashboardEnseignantView.as_view(),
        name="dashboard_enseignant",
    ),
    path(
        "dashboard/labrespo/",
        views.DashboardLabRespoView.as_view(),
        name="dashboard_labrespo",
    ),
    path(
        "dashboard/service-achat/",
        views.DashboardServiceAchatView.as_view(),
        name="dashboard_service_achat",
    ),
    path(
        "dashboard/service3ph/",
        views.DashboardService3PHView.as_view(),
        name="dashboard_service3ph",
    ),
    path("materiels/", views.MaterielListView.as_view(), name="materiel_list"),
    path("materiels/<int:pk>/", views.materiel_detail, name="materiel_detail"),
    path("materiels/ajouter/", views.MaterielCreateView.as_view(), name="materiel_create"),
    path("materiels/<int:pk>/modifier/", views.MaterielUpdateView.as_view(), name="materiel_update"),
    path("materiels/<int:pk>/supprimer/", views.MaterielDeleteView.as_view(), name="materiel_delete"),
    path("demandes/", views.DemandeListView.as_view(), name="demande_list"),
    path("demandes/<int:pk>/", views.demande_detail, name="demande_detail"),
    path(
        "demandes/creer/existant/",
        views.demande_existant_create,
        name="demande_existant_create",
    ),
    path("demandes/creer/nouveau/", views.demande_nouveau_create, name="demande_nouveau_create"),
    path(
        "demandes/<int:pk>/commenter/",
        views.teacher_comment_demande,
        name="teacher_comment_demande",
    ),
    path(
        "demandes/<int:pk>/decision/",
        views.labrespo_decision_demande,
        name="labrespo_decision_demande",
    ),
    path("demandes/<int:pk>/sortie/", views.confirmer_sortie, name="confirmer_sortie"),
    path("demandes/<int:pk>/retour/", views.confirmer_retour, name="confirmer_retour"),
    path(
        "demandes/<int:pk>/decision-achat/",
        views.service_achat_decision_demande,
        name="service_achat_decision_demande",
    ),
    path("mouvements/", views.MouvementStockListView.as_view(), name="mouvement_list"),
    path("enseignant/groupes/", views.teacher_groups, name="teacher_group_list"),
    path("groupes/<int:pk>/", views.group_detail, name="group_detail"),
    path("service/groupes/", views.GroupeListServiceView.as_view(), name="service_group_list"),
    path(
        "service/enseignants/",
        views.EnseignantListServiceView.as_view(),
        name="service_teacher_list",
    ),
    path(
        "service/affectations/creer/",
        views.AffectationCreateView.as_view(),
        name="affectation_create",
    ),
    path(
        "service/affectations/<int:pk>/modifier/",
        views.AffectationUpdateView.as_view(),
        name="affectation_update",
    ),
]
