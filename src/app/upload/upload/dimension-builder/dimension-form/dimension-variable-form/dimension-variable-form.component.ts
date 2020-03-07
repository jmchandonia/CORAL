import { Component, OnInit, Input, Output, EventEmitter, OnDestroy, ViewEncapsulation } from '@angular/core';
import { BrickDimension, DimensionVariable, Term, Context } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';
import { BsModalService, BsModalRef } from 'ngx-bootstrap';
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
      } else {
        this.typeData = [d.typeTerm];
      }
      this.selectedType = d.typeTerm.id;
    }

    if (d.units) {
      this.unitsData = [d.units];
      this.selectedUnits = d.units.id;
    }
  }

  get dimVar() {
    return this._dimVar;
  }

  typeData: Array<Select2OptionData> = [];
  unitsData: Array<Select2OptionData> = [{id: '', text: ''}];
  selectedType: string;
  selectedUnits: string;
  error = false;
  modalRef: BsModalRef;
  errorSub: Subscription;

  private _dimVar: DimensionVariable;

  @Output() deleted: EventEmitter<DimensionVariable> = new EventEmitter();
  @Output() reset: EventEmitter<DimensionVariable> = new EventEmitter();

  typeOptions: Select2Options = {
    width: 'calc(100% - 38px)',
    containerCssClass: 'select2-custom-container select2-custom-properties-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term) {
        options.callback({results: []});
      } else {
        this.uploadService.searchDimensionVariableMicroTypes(term)
          .subscribe((data: any) => {
            options.callback({results: data.results as Select2OptionData});
          });
      }
    }
  };

  unitsOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
  };

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

  setContextLabel(dimVarType: Term, context: Context[]): Select2OptionData {
    const label: Select2OptionData = Object.assign({}, dimVarType);
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
    const term = event.data[0];
    this.dimVar.typeTerm = term;
    if (!term.has_units) {
      this.dimVar.units = null;
    } else {
      this.dimVar.units = undefined;
      this.uploadService.searchOntPropertyUnits(this.dimVar.microType)
        .subscribe(data => {
          this.unitsData = data.results;
        });
    }
    this.validate();
  }

  setDimVarUnits(event) {
    const term = event.data[0];
    this.dimVar.units = new Term(term.id, term.text);
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
      this.reset.emit(newDimVar);
      modalSub.unsubscribe();
    });
  }

}
