import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, ViewEncapsulation } from '@angular/core';
import { TypedProperty, Term } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';
// tslint:disable:variable-name

@Component({
  selector: 'app-property-form',
  templateUrl: './property-form.component.html',
  styleUrls: ['./property-form.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class PropertyFormComponent implements OnInit, OnDestroy {
  selectedValue: any;
  @Output() deleted = new EventEmitter();
  @Output() typeReselected: EventEmitter<TypedProperty> = new EventEmitter();
  @Input() set property(prop: TypedProperty) {

    this.typesSelect2 = prop.type ? [prop.type] : [];
    this.unitsSelect2 = prop.units ? [prop.units] : [{id: '', text: ''}];
    this.valuesSelect2 = prop.value ? [prop.value] : [{id: '', text: ''}];

    this._property = prop;

    if (prop.type) {
      this.propTypeItem = prop.type.id;
    }
    if (prop.units) {
      this.unitsItem = prop.units.id;
    }
    if (prop.value) {
      this.propValueItem = prop.value.id;
    }

    if (this.property.microType) {
      this.getPropertyUnits();
    }
  }

  get property() {
    return  this._property;
  }

  get valueItem() {
    return this.property.value ?
      this.property.value.text : '';
  }

  private _property: TypedProperty;

  propertiesOptions: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term || term.length < 3) {
        options.callback({results: []});
      } else {
        this.uploadService.searchPropertyMicroTypes(term).subscribe((data: any) => {
          options.callback({results: data.results as Select2OptionData});
        });
      }
    }
   };

   valuesOptions: Select2Options = {
     width: '100%',
     containerCssClass: 'select2-custom-container',
     query: (options: Select2QueryOptions) => {
       const term = options.term;
       if (!term || term.length < 3) {
         options.callback({results: []});
       } else {
         this.uploadService.searchOntPropertyValues(term, this.property.microType) // ADD POST DATA
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


   typesSelect2: Array<Select2OptionData> = [];
   unitsSelect2: Array<Select2OptionData> = [{ id: '', text: '' }];
   valuesSelect2: Array<Select2OptionData> = [{ id: '', text: '' }];

   errorSub = new Subscription();
   propTypeItem: string;
   propValueItem: string;
   unitsItem: string;
   required = true;
   errors = false;

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService
  ) { }

  ngOnInit() {
    this.errorSub = this.validator.getValidationErrors()
      .subscribe(errors => {
        if (!this.property.required) {
          this.errors = errors;
        }
      });
  }

  ngOnDestroy() {
    if (this.errorSub) {
      this.errorSub.unsubscribe();
    }
  }

  delete() {
    this.deleted.emit();
  }

  getPropertyUnits() {
    this.uploadService.searchOntPropertyUnits(this.property.microType)
      .subscribe(data => {
        if (!data.results.length) {
          this.property.units = null as Term;
        } else {
          if (this.property.units === null) {
            this.property.units = undefined;
          }
          this.unitsSelect2 = [...this.unitsSelect2, ...data.results];
        }
      });
  }

  setPropertyType(event) {
    const item = event.data[0];
    this.property.type = new Term(item.id, item.text);
    this.property.microType = item.microtype;

    // clear reset entire property object to clear other select 2 dropdowns
    if (this.property.value || this.property.units) {
      const resetProperty = new TypedProperty(
        this.property.index,
        this.property.required,
        this.property.type,
        this.property.microType
      );
      // emit new typed property to replace old one in parent component array reference
      this.typeReselected.emit(resetProperty);
    } else {
      this.getPropertyUnits();
    }
  }

  setValue(event) {
    const item = event.data[0];
    this.property.value = new Term(item.id, item.text);
  }

  setUnits(event) {
    const item = event.data[0];
    this.property.units = new Term(item.id, item.text);
  }

  onDelete() {
    this.deleted.emit(this.property);
  }

}
