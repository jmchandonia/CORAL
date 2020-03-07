import { Component, OnInit, OnDestroy, Input, ViewEncapsulation,EventEmitter, Output } from '@angular/core';
import { DataValue, Term, Context } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';
import { BsModalRef, BsModalService } from 'ngx-bootstrap/modal';
import { ContextBuilderComponent } from 'src/app/upload/upload/property-builder/property-form/context-builder/context-builder.component';

@Component({
  selector: 'app-data-value-form',
  templateUrl: './data-value-form.component.html',
  styleUrls: ['./data-value-form.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class DataValueFormComponent implements OnInit, OnDestroy {

  @Input() set dataValue(d: DataValue) {
    this._dataValue = d;

    if (d.typeTerm) {
      if (d.context && d.context.length) {
        this.typeValues = [this.setContextLabel(d.typeTerm, d.context)];
      } else {
        this.typeValues = [d.typeTerm];
      }
      this.typeValuesItem = d.typeTerm.id;
    }

    if (d.units) {
      this.unitsValues = [d.units];
      this.unitsItem = d.units.id;
    }

    if (d.microType) {
      this.getUnits();
    }
  }

  get dataValue() { return this._dataValue; }

  @Output() removed: EventEmitter<any> = new EventEmitter();
  @Output() reset: EventEmitter<any> = new EventEmitter();

  // tslint:disable-next-line:variable-name
  private _dataValue: DataValue;

  typeValues: Array<Select2OptionData> = [{id: '', text: ''}];
  unitsValues: Array<Select2OptionData> = [{id: '', text: ''}];

  typeValuesItem: string;
  unitsItem: string;
  error = false;
  errorSub: Subscription;
  modalRef: BsModalRef;

   unitsOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
   };

   typesOptions: Select2Options = {
    width: 'calc(100% - 38px)',
    containerCssClass: 'select2-custom-container select2-custom-properties-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term) {
        options.callback({results: []});
      } else {
        this.uploadService.searchDataVariableMicroTypes(term).subscribe((data: any) => {
          options.callback({results: data.results as Select2OptionData});
        });
      }
    }
   };

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService,
    private modalService: BsModalService
  ) { }

  ngOnInit() {
    this.errorSub = this.validator.getValidationErrors()
      .subscribe(error => {
        if (!this.dataValue.required) {
          this.error = error;
        }
      });
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  setContextLabel(dataType: Term, context: Context[]) {
    const label: Select2OptionData = Object.assign({}, dataType);
    context.forEach(ctx => {
      const { typeTerm, value, units } = ctx;
      label.text += `, ${typeTerm.text}=${value.text ? value.text : value}`;
      if (units) {
        label.text += ` (${units.text})`;
      }
    });
    return label;
  }

  onDelete() {
    this.removed.emit();
    this.validate();
  }

  updateType(event) {
    const type = event.data[0];
    this.dataValue.typeTerm = type;
    if (!type.has_units) {
      this.dataValue.units = null;
    } else {
      this.dataValue.units = undefined;
      this.getUnits();
    }
    this.validate();
  }

  getUnits() {
    this.uploadService.searchOntPropertyUnits(this.dataValue.microType)
      .subscribe(data => {
        this.unitsValues = [this.unitsValues[0], ...data.results];
      });
  }

  updateUnits(event) {
    if (event.value.length) {
      const units = event.data[0];
      this.dataValue.units = new Term(units.id, units.text);
      this.validate();
    }
  }

  validate() {
    if (this.error) {
      this.validator.validateDataVariables();
    }
  }

  openContextModal() {
    const config = {
      initialState: {
        context: this.dataValue.context,
        title: this.dataValue.typeTerm.text
      },
      class: 'modal-lg',
      ignoreBackdropClick: true
    };
    this.modalRef = this.modalService.show(ContextBuilderComponent, config);
    const modalSub = this.modalService.onHidden.subscribe(() => {
      const newDataVar = Object.assign(
        new DataValue(this.dataValue.index, this.dataValue.required), this.dataValue
        ) as DataValue;
      this.reset.emit(newDataVar);
      modalSub.unsubscribe();
    });
  }

}
