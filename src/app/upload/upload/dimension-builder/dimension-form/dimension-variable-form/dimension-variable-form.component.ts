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
    if (d.type) {
      if (d.context.length) {
        this.typeData = [this.setContextLabel(d.type, d.context[0])];
      } else {
        this.typeData = [d.type];
      }
      this.selectedType = d.type.id;
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

  typeOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
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

  setContextLabel(label: Term, context: Context) {
    // const label = type;
    const { type, value, units } = context;
    label.text += `, ${type.text}=${value.text}`;
    if (units) {
      label.text += ` (${units.text})`;
    }
    return label;
  }

  delete() {
    this.deleted.emit(this.dimVar);
  }

  setDimVarType(event) {
    const term = event.data[0];
    this.dimVar.type = term;
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
    const initialState = {
      context: this.dimVar.context
    };
    this.modalRef = this.modalService.show(ContextBuilderComponent, { initialState, class: 'modal-lg' });
  }

}
