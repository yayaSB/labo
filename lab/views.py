from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView
from django.utils import timezone

from .forms import (
    AffectationGroupeForm,
    DemandeExistantForm,
    DemandeNouveauMaterielForm,
    DemandeNouveauParentForm,
    LabRespoDecisionForm,
    LigneDemandeFormSet,
    MaterielForm,
    TeacherDecisionForm,
)
from .mixins import RoleRequiredMixin
from .models import AffectationGroupe, Demande, Groupe, Materiel, MouvementStock, User


def _role_dashboard_name(role):
    return {
        User.Role.ETUDIANT: "dashboard_etudiant",
        User.Role.ENCADRANT: "dashboard_enseignant",
        User.Role.ENSEIGNANT: "dashboard_enseignant",
        User.Role.LABO_TEMPS: "dashboard_labrespo",
        User.Role.LABRESPO: "dashboard_labrespo",
        User.Role.SERVICE_3PH: "dashboard_service3ph",
    }.get(role, "login")


def _teacher_group_ids(enseignant):
    return AffectationGroupe.objects.filter(enseignant=enseignant).values_list(
        "groupe_id", flat=True
    )


def _is_group_teacher(user, groupe_id):
    return AffectationGroupe.objects.filter(enseignant=user, groupe_id=groupe_id).exists()


LABRESPO_MANAGEABLE_STATUSES = {
    Demande.Statut.VALIDEE_PAR_ENSEIGNANT,
    Demande.Statut.EN_COURS_TRAITEMENT,
    Demande.Statut.EN_PAUSE,
    Demande.Statut.DISPONIBLE,
    Demande.Statut.RETIREE,
}


def _labrespo_status_choices(demande):
    choices = [
        (Demande.Statut.EN_COURS_TRAITEMENT, "Mettre en cours de traitement"),
        (Demande.Statut.EN_PAUSE, "Mettre en pause"),
        (Demande.Statut.DISPONIBLE, "Marquer disponible"),
        (Demande.Statut.REFUSEE, "Refuser"),
        (Demande.Statut.TERMINEE, "Terminer"),
    ]
    if demande.type_demande == Demande.TypeDemande.EXISTANT:
        choices.insert(3, (Demande.Statut.RETIREE, "Marquer retiree"))
    return choices


@login_required
def role_redirect(request):
    return redirect(_role_dashboard_name(request.user.role))


class DashboardEtudiantView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/etudiant_dashboard.html"
    required_roles = [User.Role.ETUDIANT]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        demandes = Demande.objects.filter(etudiant=self.request.user)
        context["stats"] = {
            "total": demandes.count(),
            "en_attente": demandes.filter(
                statut=Demande.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT
            ).count(),
            "validees": demandes.filter(
                statut=Demande.Statut.VALIDEE_PAR_ENSEIGNANT
            ).count(),
            "en_cours": demandes.filter(
                statut__in=[
                    Demande.Statut.EN_COURS_TRAITEMENT,
                    Demande.Statut.EN_PAUSE,
                    Demande.Statut.DISPONIBLE,
                    Demande.Statut.RETIREE,
                ]
            ).count(),
        }
        context["dernieres_demandes"] = demandes[:5]
        context["groupes"] = Groupe.objects.filter(membres__etudiant=self.request.user).distinct()
        return context


class DashboardEnseignantView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/enseignant_dashboard.html"
    required_roles = [User.Role.ENSEIGNANT, User.Role.ENCADRANT]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group_ids = _teacher_group_ids(self.request.user)
        demandes = Demande.objects.filter(groupe_id__in=group_ids)
        context["stats"] = {
            "groupes": group_ids.count(),
            "demandes": demandes.count(),
            "a_commenter": demandes.filter(
                statut=Demande.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT
            ).count(),
            "en_attente_lab": demandes.filter(
                statut=Demande.Statut.VALIDEE_PAR_ENSEIGNANT
            ).count(),
        }
        context["demandes"] = demandes[:8]
        return context


class DashboardLabRespoView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/labrespo_dashboard.html"
    required_roles = [User.Role.LABRESPO, User.Role.LABO_TEMPS]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        demandes = Demande.objects.all()
        today = timezone.localdate()
        context["stats"] = {
            "materiels": Materiel.objects.count(),
            "stock_faible": Materiel.objects.filter(
                quantite_disponible__lte=models.F("seuil_alerte")
            ).count(),
            "en_attente": demandes.filter(
                statut=Demande.Statut.VALIDEE_PAR_ENSEIGNANT
            ).count(),
            "validees": demandes.filter(
                statut=Demande.Statut.DISPONIBLE
            ).count(),
            "retards": demandes.filter(
                statut__in=[
                    Demande.Statut.EN_COURS_TRAITEMENT,
                    Demande.Statut.EN_PAUSE,
                    Demande.Statut.DISPONIBLE,
                    Demande.Statut.RETIREE,
                ],
                date_souhaitee_retour__lt=today,
            ).count(),
        }
        context["demandes_recentes"] = demandes[:10]
        return context


class DashboardService3PHView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/service3ph_dashboard.html"
    required_roles = [User.Role.SERVICE_3PH]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = {
            "groupes": Groupe.objects.count(),
            "etudiants": User.objects.filter(role=User.Role.ETUDIANT).count(),
            "enseignants": User.objects.filter(role=User.Role.ENSEIGNANT).count(),
            "affectations": AffectationGroupe.objects.count(),
        }
        context["demandes"] = Demande.objects.select_related("etudiant", "groupe")[:10]
        return context


class MaterielListView(RoleRequiredMixin, ListView):
    model = Materiel
    template_name = "materials/materiel_list.html"
    context_object_name = "materiels"
    required_roles = [User.Role.ETUDIANT, User.Role.LABRESPO]

    def get_queryset(self):
        queryset = super().get_queryset()
        categorie = self.request.GET.get("categorie")
        if categorie:
            queryset = queryset.filter(categorie__iexact=categorie)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = (
            Materiel.objects.exclude(categorie="")
            .values_list("categorie", flat=True)
            .distinct()
            .order_by("categorie")
        )
        return context


@login_required
def materiel_detail(request, pk):
    materiel = get_object_or_404(Materiel, pk=pk)
    if request.user.role not in [User.Role.ETUDIANT, User.Role.LABRESPO]:
        return HttpResponseForbidden("Acces interdit")
    return render(request, "materials/materiel_detail.html", {"materiel": materiel})


class MaterielCreateView(RoleRequiredMixin, CreateView):
    model = Materiel
    form_class = MaterielForm
    template_name = "materials/materiel_form.html"
    success_url = reverse_lazy("materiel_list")
    required_roles = [User.Role.LABRESPO]


class MaterielUpdateView(RoleRequiredMixin, UpdateView):
    model = Materiel
    form_class = MaterielForm
    template_name = "materials/materiel_form.html"
    success_url = reverse_lazy("materiel_list")
    required_roles = [User.Role.LABRESPO]


class MaterielDeleteView(RoleRequiredMixin, DeleteView):
    model = Materiel
    template_name = "materials/materiel_confirm_delete.html"
    success_url = reverse_lazy("materiel_list")
    required_roles = [User.Role.LABRESPO]


@login_required
def demande_existant_create(request):
    if request.user.role != User.Role.ETUDIANT:
        return HttpResponseForbidden("Acces interdit")

    demande = Demande(
        etudiant=request.user,
        type_demande=Demande.TypeDemande.EXISTANT,
        statut=Demande.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT,
    )

    if request.method == "POST":
        form = DemandeExistantForm(
            request.POST,
            etudiant=request.user,
            instance=demande,
        )
        formset = LigneDemandeFormSet(request.POST, instance=demande)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                demande = form.save(commit=False)
                demande.etudiant = request.user
                demande.type_demande = Demande.TypeDemande.EXISTANT
                demande.statut = Demande.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT
                demande.save()
                formset.instance = demande
                formset.save()
            messages.success(request, "Demande de materiel existant creee.")
            return redirect("demande_detail", pk=demande.pk)
    else:
        form = DemandeExistantForm(etudiant=request.user, instance=demande)
        formset = LigneDemandeFormSet(instance=demande)

    return render(
        request,
        "demands/demande_existant_form.html",
        {"form": form, "formset": formset},
    )


@login_required
def demande_nouveau_create(request):
    if request.user.role != User.Role.ETUDIANT:
        return HttpResponseForbidden("Acces interdit")

    demande = Demande(
        etudiant=request.user,
        type_demande=Demande.TypeDemande.NOUVEAU,
        statut=Demande.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT,
    )

    if request.method == "POST":
        parent_form = DemandeNouveauParentForm(
            request.POST,
            etudiant=request.user,
            instance=demande,
        )
        child_form = DemandeNouveauMaterielForm(request.POST)
        if parent_form.is_valid() and child_form.is_valid():
            with transaction.atomic():
                demande = parent_form.save(commit=False)
                demande.etudiant = request.user
                demande.type_demande = Demande.TypeDemande.NOUVEAU
                demande.statut = Demande.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT
                demande.save()
                nouveau = child_form.save(commit=False)
                nouveau.demande = demande
                nouveau.save()
            messages.success(request, "Demande de nouveau materiel soumise.")
            return redirect("demande_detail", pk=demande.pk)
    else:
        parent_form = DemandeNouveauParentForm(etudiant=request.user, instance=demande)
        child_form = DemandeNouveauMaterielForm()

    return render(
        request,
        "demands/demande_nouveau_form.html",
        {"parent_form": parent_form, "child_form": child_form},
    )


class DemandeListView(RoleRequiredMixin, ListView):
    model = Demande
    template_name = "demands/demande_list.html"
    context_object_name = "demandes"
    required_roles = [
        User.Role.ETUDIANT,
        User.Role.ENCADRANT,
        User.Role.ENSEIGNANT,
        User.Role.LABO_TEMPS,
        User.Role.LABRESPO,
        User.Role.SERVICE_3PH,
    ]

    def get_queryset(self):
        user = self.request.user
        queryset = Demande.objects.select_related("etudiant", "groupe")
        if user.role == User.Role.ETUDIANT:
            queryset = queryset.filter(etudiant=user)
        elif user.role in [User.Role.ENSEIGNANT, User.Role.ENCADRANT]:
            queryset = queryset.filter(groupe_id__in=_teacher_group_ids(user))
        return queryset


@login_required
def demande_detail(request, pk):
    demande = get_object_or_404(
        Demande.objects.select_related("etudiant", "groupe").prefetch_related(
            "lignes_demande__materiel"
        ),
        pk=pk,
    )
    user = request.user

    authorized = user.role in [User.Role.LABRESPO, User.Role.SERVICE_3PH]
    authorized = authorized or (user.role == User.Role.ETUDIANT and demande.etudiant_id == user.id)
    authorized = authorized or (
        user.role in [User.Role.ENSEIGNANT, User.Role.ENCADRANT]
        and _is_group_teacher(user, demande.groupe_id)
    )

    if not authorized:
        return HttpResponseForbidden("Acces interdit")

    return render(request, "demands/demande_detail.html", {"demande": demande})


@login_required
def teacher_groups(request):
    if request.user.role not in [User.Role.ENSEIGNANT, User.Role.ENCADRANT]:
        return HttpResponseForbidden("Acces interdit")
    affectations = AffectationGroupe.objects.filter(enseignant=request.user).select_related(
        "groupe"
    )
    return render(request, "groups/teacher_group_list.html", {"affectations": affectations})


@login_required
def group_detail(request, pk):
    groupe = get_object_or_404(Groupe, pk=pk)
    if request.user.role in [User.Role.ENSEIGNANT, User.Role.ENCADRANT] and not _is_group_teacher(request.user, pk):
        return HttpResponseForbidden("Acces interdit")
    if request.user.role not in [User.Role.ENSEIGNANT, User.Role.ENCADRANT, User.Role.SERVICE_3PH]:
        return HttpResponseForbidden("Acces interdit")
    membres = groupe.membres.select_related("etudiant")
    demandes = groupe.demandes.select_related("etudiant")[:20]
    return render(
        request,
        "groups/group_detail.html",
        {"groupe": groupe, "membres": membres, "demandes": demandes},
    )


@login_required
def teacher_comment_demande(request, pk):
    if request.user.role not in [User.Role.ENSEIGNANT, User.Role.ENCADRANT]:
        return HttpResponseForbidden("Acces interdit")

    demande = get_object_or_404(Demande, pk=pk)
    if not _is_group_teacher(request.user, demande.groupe_id):
        return HttpResponseForbidden("Acces interdit")

    if demande.statut != Demande.Statut.EN_ATTENTE_VALIDATION_ENSEIGNANT:
        messages.warning(
            request,
            "Cette demande n'est plus en attente de validation enseignant.",
        )
        return redirect("demande_detail", pk=demande.pk)

    if request.method == "POST":
        form = TeacherDecisionForm(request.POST, instance=demande)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.statut = form.cleaned_data["statut"]
            obj.save()
            if obj.statut == Demande.Statut.VALIDEE_PAR_ENSEIGNANT:
                messages.success(request, "Demande validee pedagogiquement.")
            else:
                messages.success(request, "Demande refusee pedagogiquement.")
            return redirect("demande_detail", pk=demande.pk)
    else:
        form = TeacherDecisionForm(instance=demande)
    return render(
        request,
        "demands/teacher_comment_form.html",
        {"form": form, "demande": demande},
    )


@login_required
def labrespo_decision_demande(request, pk):
    if request.user.role not in [User.Role.LABRESPO, User.Role.LABO_TEMPS]:
        return HttpResponseForbidden("Acces interdit")
    demande = get_object_or_404(
        Demande.objects.prefetch_related("lignes_demande__materiel"), pk=pk
    )

    if demande.statut not in LABRESPO_MANAGEABLE_STATUSES:
        messages.warning(
            request,
            "Le laboratoire ne peut traiter que les demandes validees par l'enseignant ou deja en traitement.",
        )
        return redirect("demande_detail", pk=demande.pk)

    if request.method == "POST":
        form = LabRespoDecisionForm(request.POST, instance=demande)
        form.fields["statut"].choices = _labrespo_status_choices(demande)
        if form.is_valid():
            decision = form.cleaned_data["statut"]
            demande = form.save(commit=False)

            if decision == Demande.Statut.DISPONIBLE and demande.type_demande == Demande.TypeDemande.EXISTANT:
                for ligne in demande.lignes_demande.all():
                    if ligne.materiel.quantite_disponible < ligne.quantite_demandee:
                        messages.error(
                            request,
                            f"Stock insuffisant pour {ligne.materiel.nom}.",
                        )
                        return redirect("demande_detail", pk=demande.pk)
                    ligne.quantite_validee = ligne.quantite_demandee
                    ligne.save()

            if decision == Demande.Statut.RETIREE and demande.type_demande == Demande.TypeDemande.NOUVEAU:
                messages.error(
                    request,
                    "Le statut RETIREE est reserve aux demandes de materiel existant.",
                )
                return redirect("demande_detail", pk=demande.pk)

            demande.statut = decision
            demande.save()
            messages.success(request, "Statut laboratoire mis a jour.")
            return redirect("demande_detail", pk=demande.pk)
    else:
        form = LabRespoDecisionForm(instance=demande)
        form.fields["statut"].choices = _labrespo_status_choices(demande)

    return render(
        request,
        "demands/labrespo_decision_form.html",
        {"form": form, "demande": demande},
    )


@login_required
def confirmer_sortie(request, pk):
    if request.user.role not in [User.Role.LABRESPO, User.Role.LABO_TEMPS]:
        return HttpResponseForbidden("Acces interdit")

    demande = get_object_or_404(
        Demande.objects.prefetch_related("lignes_demande__materiel"), pk=pk
    )
    if demande.type_demande != Demande.TypeDemande.EXISTANT:
        messages.error(request, "Action reservee aux demandes de materiel existant.")
        return redirect("demande_detail", pk=pk)

    if demande.statut != Demande.Statut.DISPONIBLE:
        messages.error(request, "Le statut doit etre DISPONIBLE avant retrait.")
        return redirect("demande_detail", pk=pk)

    with transaction.atomic():
        for ligne in demande.lignes_demande.all():
            quantite_sortie = ligne.quantite_validee or ligne.quantite_demandee
            if ligne.materiel.quantite_disponible < quantite_sortie:
                messages.error(
                    request,
                    f"Stock insuffisant pour {ligne.materiel.nom} au moment du retrait.",
                )
                return redirect("demande_detail", pk=pk)
            ligne.materiel.quantite_disponible -= quantite_sortie
            ligne.materiel.save()
            MouvementStock.objects.create(
                materiel=ligne.materiel,
                demande=demande,
                type_mouvement=MouvementStock.TypeMouvement.SORTIE,
                quantite=quantite_sortie,
                valide_par=request.user,
            )
            if ligne.quantite_validee == 0:
                ligne.quantite_validee = quantite_sortie
                ligne.save()
        demande.statut = Demande.Statut.RETIREE
        demande.save()

    messages.success(request, "Retrait materiel confirme.")
    return redirect("demande_detail", pk=pk)


@login_required
def confirmer_retour(request, pk):
    if request.user.role not in [User.Role.LABRESPO, User.Role.LABO_TEMPS]:
        return HttpResponseForbidden("Acces interdit")
    demande = get_object_or_404(
        Demande.objects.prefetch_related("lignes_demande__materiel"), pk=pk
    )
    if demande.type_demande != Demande.TypeDemande.EXISTANT:
        messages.error(request, "Action reservee aux demandes de materiel existant.")
        return redirect("demande_detail", pk=pk)

    if demande.statut != Demande.Statut.RETIREE:
        messages.error(request, "Le retour n'est possible qu'apres retrait.")
        return redirect("demande_detail", pk=pk)

    with transaction.atomic():
        for ligne in demande.lignes_demande.all():
            quantite_retour = ligne.quantite_validee or ligne.quantite_demandee
            ligne.materiel.quantite_disponible += quantite_retour
            if ligne.materiel.quantite_disponible > ligne.materiel.quantite_totale:
                ligne.materiel.quantite_disponible = ligne.materiel.quantite_totale
            ligne.materiel.save()
            MouvementStock.objects.create(
                materiel=ligne.materiel,
                demande=demande,
                type_mouvement=MouvementStock.TypeMouvement.RETOUR,
                quantite=quantite_retour,
                valide_par=request.user,
            )
        demande.statut = Demande.Statut.TERMINEE
        demande.save()

    messages.success(request, "Retour confirme et demande terminee.")
    return redirect("demande_detail", pk=pk)


class MouvementStockListView(RoleRequiredMixin, ListView):
    model = MouvementStock
    template_name = "materials/mouvement_list.html"
    context_object_name = "mouvements"
    required_roles = [User.Role.LABRESPO, User.Role.LABO_TEMPS]

    def get_queryset(self):
        return MouvementStock.objects.select_related("materiel", "demande", "valide_par")


class GroupeListServiceView(RoleRequiredMixin, ListView):
    model = Groupe
    template_name = "groups/service_group_list.html"
    context_object_name = "groupes"
    required_roles = [User.Role.SERVICE_3PH]

    def get_queryset(self):
        return (
            Groupe.objects.all()
            .annotate(nb_etudiants=Count("membres"))
            .select_related("affectation__enseignant")
        )


class EnseignantListServiceView(RoleRequiredMixin, ListView):
    model = User
    template_name = "groups/service_teacher_list.html"
    context_object_name = "enseignants"
    required_roles = [User.Role.SERVICE_3PH]

    def get_queryset(self):
        return User.objects.filter(role__in=[User.Role.ENSEIGNANT, User.Role.ENCADRANT])


class AffectationCreateView(RoleRequiredMixin, CreateView):
    model = AffectationGroupe
    form_class = AffectationGroupeForm
    template_name = "groups/affectation_form.html"
    success_url = reverse_lazy("service_group_list")
    required_roles = [User.Role.SERVICE_3PH]

    def form_valid(self, form):
        form.instance.attribue_par = self.request.user
        messages.success(self.request, "Affectation creee.")
        return super().form_valid(form)


class AffectationUpdateView(RoleRequiredMixin, UpdateView):
    model = AffectationGroupe
    form_class = AffectationGroupeForm
    template_name = "groups/affectation_form.html"
    success_url = reverse_lazy("service_group_list")
    required_roles = [User.Role.SERVICE_3PH]

    def form_valid(self, form):
        form.instance.attribue_par = self.request.user
        messages.success(self.request, "Affectation mise a jour.")
        return super().form_valid(form)
