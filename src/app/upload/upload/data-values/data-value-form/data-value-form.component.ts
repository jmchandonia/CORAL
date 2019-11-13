import { Component, OnInit, OnDestroy, Input, ViewEncapsulation,EventEmitter, Output } from '@angular/core';
import { DataValue, Term, Context } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-data-value-form',
  templateUrl: './data-value-form.component.html',
  styleUrls: ['./data-value-form.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class DataValueFormComponent implements OnInit, OnDestroy {

  @Input() set dataValue(d: DataValue) {
    this._dataValue = d;

    if (d.type) {
      if (d.context && d.context.length) {
        this.typeValues = [this.setContextLabel(d.type, d.context[0])];
      } else {
        this.typeValues = [d.type];
      }
      this.typeValuesItem = d.type.id;
    }

    if (d.units) {
      this.unitsValues = [d.units];
      this.unitsItem = d.units.id;
    }
  }

  get dataValue() { return this._dataValue; }

  @Output() removed: EventEmitter<any> = new EventEmitter();

  // tslint:disable-next-line:variable-name
  private _dataValue: DataValue;

  typeValues: Array<Select2OptionData> = [{id: '', text: ''}];
  unitsValues: Array<Select2OptionData> = [{id: '', text: ''}];

  typeValuesItem: string;
  unitsItem: string;
  error = false;
  errorSub: Subscription;

   unitsOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
   };

   typesOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
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
    private validator: UploadValidationService
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

  setContextLabel(type: Term, context: Context) {
    const label: Select2OptionData = Object.assign({}, type);
    const { property, value, units } = context;
    label.text += `, ${property.text}=${value.text}`;
    if (units) {
      label.text += ` (${units.text})`;
    }
    return label;
  }

  onDelete() {
    this.removed.emit();
    this.validate();
  }

  updateType(event) {
    const type = event.data[0];
    this.dataValue.type = type;
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
        this.unitsValues = [{id: '', text: ''}, ...data.results];
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

}
