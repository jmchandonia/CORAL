import { Component, OnInit, Input, Output, EventEmitter, OnDestroy, ViewEncapsulation } from '@angular/core';
import { BrickDimension, DimensionVariable, Term, Context } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { ContextBuilderComponent } from 'src/app/upload/upload/property-builder/property-form/context-builder/context-builder.component';

@Component({
  selector: 'app-dimension-variable-form',
  templateUrl: './dimension-variable-form.component.html',
  styleUrls: ['./dimension-variable-form.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class DimensionVariableFormComponent implements OnInit, OnDestroy {

  @Input() set dimVar(d: DimensionVariable) {
    this._dimVar = d;
    if (d.typeTerm) {
      if (d.context.length) {
        this.typeData = [this.setContextLabel(d.typeTerm, d.context)];
        // this.getDimVarUnits();
      } else {
        this.typeData = [d.typeTerm];
      }
      this.selectedType = d.typeTerm.id;
    }

    if (d.units) {
      this.unitsData = [d.units];
      this.selectedUnits = d.units.id;
    }

    if (d.unitOptions) {
      this.unitsData = d.unitOptions
    }
  }

  get dimVar() {
    return this._dimVar;
  }

  typeData: Array<Term> = [];
  unitsData: Array<Term> = [];
  selectedType: string;
  selectedUnits: string;
  error = false;
  modalRef: BsModalRef;
  errorSub: Subscription;
  typeLoading = false;
  unitsLoading = false;

  private _dimVar: DimensionVariable;

  @Output() deleted: EventEmitter<DimensionVariable> = new EventEmitter();
  @Output() reset: EventEmitter<DimensionVariable> = new EventEmitter();

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService,
    private modalService: BsModalService
  ) { }

  ngOnInit() {
    this.errorSub = this.validator.getValidationErrors()
      .subscribe(error => {
        if (!this.dimVar.required) {
          this.error = error;
        }
      });
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  handleSearch(event) {
    if (event.term.length) {
      this.typeLoading = true;
      this.uploadService.searchDimensionMicroTypes(event.term).subscribe((data: any) => {
        this.typeData = [...data.results];
        this.typeLoading = false;
      });
    }
  } 

  formatOptionLabel(item) {
    // format for displaying microtype dropdown options
    return `${item.definition !== `${item.text}.` ? ` - ${item.definition}` : ''} (${item.scalar_type})`;
  }

  setContextLabel(dimVarType: Term, context: Context[]): Term {
    const label: Term = Object.assign({}, dimVarType);
    context.forEach(ctx => {
      const { typeTerm, value, units } = ctx;
      label.text += `, ${typeTerm.text}=${value.text ? value.text : value}`;
      if (units) {
        label.text += ` (${units.text})`;
      }
    });
    return label;
  }

  delete() {
    this.deleted.emit(this.dimVar);
  }

  setDimVarType(event) {
    const term = event;
    this.dimVar.typeTerm = term;
    if (!term.has_units) {
      this.dimVar.units = null;
    } else {
      this.dimVar.units = undefined;
      this.getDimVarUnits();
    }
    this.validate();
  }

  getDimVarUnits() {
    this.unitsLoading = true;
    this.uploadService.searchOntPropertyUnits(this.dimVar.microType)
      .subscribe(data => {
        this.unitsData = [...data.results];
        this.unitsLoading = false;
      });
  }

  setDimVarUnits(event: Term) {
    this.dimVar.units = event;
    this.validate();
  }

  validate() {
    if (this.error) {
      this.validator.validateDimensions();
    }
  }

  openModal() {
    const config = {
      initialState: {
        context: this.dimVar.context,
        title: this.dimVar.typeTerm.text
      },
      class: 'modal-lg',
      ignoreBackdropClick: true
    };
    this.modalRef = this.modalService.show(ContextBuilderComponent, config);
    const modalSub = this.modalService.onHidden.subscribe(() => {
      const newDimVar = Object.assign(
        new DimensionVariable(this.dimVar.dimension, this.dimVar.index, this.dimVar.required),
        this.dimVar
      ) as DimensionVariable;
      newDimVar.unitOptions = this.unitsData
      this.reset.emit(newDimVar);
      modalSub.unsubscribe();
    });
  }

}
