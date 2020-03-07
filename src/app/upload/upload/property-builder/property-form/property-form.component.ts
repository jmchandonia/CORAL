import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, ViewEncapsulation } from '@angular/core';
import { TypedProperty, Term, Context } from 'src/app/shared/models/brick';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';
import { BsModalRef, BsModalService } from 'ngx-bootstrap';
import { ContextBuilderComponent } from './context-builder/context-builder.component';
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
  @Output() valueError: EventEmitter<any> = new EventEmitter();
  @Input() set property(prop: TypedProperty) {
    // this.typesSelect2 = prop.type ? [prop.type] : [];
    this.unitsSelect2 = prop.units ? [prop.units] : [{id: '', text: ''}];
    this.valuesSelect2 = prop.value && prop.requireSelect2ForVal
      ? [prop.value] as Select2OptionData[]
      : [{id: '', text: ''}];

    this._property = prop;

    if (prop.typeTerm) {
      const typeWithContext = Object.assign({}, prop.typeTerm);
      prop.context.forEach(ctx => {
        typeWithContext.text += `, ${ctx.typeTerm.text}=${ctx.value.text ? ctx.value.text : ctx.value}`;
      });
      this.typesSelect2 = [typeWithContext];
      this.propTypeItem = prop.typeTerm.id;
    }
    if (prop.units) {
      this.unitsItem = prop.units.id;
    }
    if (prop.value && prop.requireSelect2ForVal) {
      this.propValueItem = (prop.value as Term).id;
    }

    if (this.property.microType) {
      this.getPropertyUnits();
    }
  }

  get property() {
    return  this._property;
  }

  // get valueItem() {
  //   return this.property.value ?
  //     this.property.value.text : '';
  // }


  private _property: TypedProperty;

  propertiesOptions: Select2Options = {
    width: 'calc(100% - 38px)',
    containerCssClass: 'select2-custom-container select2-custom-properties-container',
    query: (options: Select2QueryOptions) => {
      const term = options.term;
      if (!term) {
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
       if (!term) {
         options.callback({results: []});
       } else {
          if (this.property.scalarType === 'oterm_ref') {
            this.uploadService.searchOntPropertyValues(term, this.property.microType)
            .subscribe((data: any) => {
              options.callback({results: data.results as Select2OptionData});
            });
          } else {
            // property scalar type is object_ref
            this.uploadService.searchPropertyValueObjectRefs(term, this.property.type.id, this.property.microType)
              .subscribe((data: any) => {
                options.callback({results: data.results as Select2OptionData});
              });
          }
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

   modalRef: BsModalRef;
   errorSub = new Subscription();
   modalHiddenSub = new Subscription();
   propTypeItem: string;
   propValueItem: string;
   unitsItem: string;
   required = true;
   errors = false;
   scalarError = false;

  constructor(
    private uploadService: UploadService,
    private validator: UploadValidationService,
    private modalService: BsModalService,
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

  openContextModal() {
    const config = {
      initialState: {
        context: this.property.context,
        title: this.property.typeTerm.text
      },
      class: 'modal-lg',
      ignoreBackdropClick: true
    };
    this.modalRef = this.modalService.show(ContextBuilderComponent, config);
    this.modalHiddenSub = this.modalService.onHidden
    .subscribe(() => {
      /*
      The following code will allow the preselected value in the types select2 component to be updated with
      a new string value containing the context. the only way this can be easily accomplished is to remove
      the entire typed property, splice in a new one with the same properties, and trigger the input setters.
      This appears to be the simplest way to programmatically change the selected text in an ng2-select2
      component without going into the internals.
      */
      const { typeTerm, index, required }  = this.property;
      const newProperty = Object.assign(
        new TypedProperty(index, required, typeTerm), this.property
        ) as TypedProperty;
      this.typeReselected.emit(newProperty);
      this.modalHiddenSub.unsubscribe();
    });
  }

  setPropertyType(event) {
    const item = event.data[0];
    this.property.typeTerm = item;

    // clear reset entire property object to clear other select 2 dropdowns
    if (this.property.value || this.property.units) {
      const resetProperty = new TypedProperty(
        this.property.index,
        this.property.required,
        item
      );
      // if (this.property.units === null) {
      //   resetProperty.units = null;
      // }
      // emit new typed property to replace old one in parent component array reference
      this.typeReselected.emit(resetProperty);
    } else {
      this.getPropertyUnits();
      this.validate();
    }
  }

  setValue(event) {
    const item = event.data[0];
    this.property.value = new Term(item.id, item.text);
    this.validate();
  }

  setUnits(event) {
    if (event.value.length) {
      const item = event.data[0];
      this.property.units = new Term(item.id, item.text);
      this.validate();
    }
  }

  onDelete() {
    this.deleted.emit(this.property);
  }

  validate() {
    if (this.errors) {
      this.validator.validateProperties();
    }
  }

  validateScalarType() {
    if (!this.validator.validScalarType(this.property.scalarType, this.property.value)) {
      // this.scalarError = true;
      this.property.invalidValue = true;
      this.valueError.emit(this.validator.INVALID_VALUE);
    } else {
      this.property.invalidValue = false;
      this.valueError.emit(null);
    }
  }

}
