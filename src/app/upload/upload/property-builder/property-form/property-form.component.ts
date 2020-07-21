import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, ViewEncapsulation } from '@angular/core';
import { TypedProperty, Term, Context } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subscription } from 'rxjs';
import { BsModalRef, BsModalService } from 'ngx-bootstrap/modal';
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
    this.unitsData = prop.units ? [prop.units] : [];
    this.valuesData = prop.value && prop.requireDropdownForVal
      ? [prop.value] as Term[] : [];

    this._property = prop;

    if (prop.type) {
      const typeWithContext = Object.assign({}, prop.type);
      prop.context.forEach(ctx => {
        typeWithContext.text += `, ${ctx.type.text}=${ctx.value.text ? ctx.value.text : ctx.value}`;
      });
      this.typesData = [typeWithContext];
      this.propTypeItem = prop.type.id;
    }
    if (prop.units) {
      this.unitsItem = prop.units.id;
    }
    if (prop.value && prop.requireDropdownForVal) {
      this.propValueItem = (prop.value as Term).id;
    }

    if (this.property.microType) {
      this.getPropertyUnits();
    }
  }

  get property() {
    return  this._property;
  }

  private _property: TypedProperty;


   typesData: Array<Term> = [];
   unitsData: Array<Term> = [];
   valuesData: Array<Term> = [];

   typesLoading = false;
   unitsLoading = false;
   valuesLoading = false;

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

  handlePropertySearch(event) {
    if (event.term.length) {
      this.typesLoading = true;
      this.uploadService.searchPropertyMicroTypes(event.term).subscribe((data: any) => {
        this.typesData = [...data.results];
        this.typesLoading = false;
      });
    }
  }

  formatOptionLabel(item) {
    // format for displaying microtype dropdown options
    return `${item.definition !== `${item.text}.` ? ` - ${item.definition}` : ''} (${item.scalar_type})`;
  }

  handleValueSearch(event) {
    if(event.term.length) {
      if(this.property.scalarType === 'oterm_ref') {
        this.uploadService.searchOntPropertyValues(event.term, this.property.microType)
          .subscribe((data: any) => {
            this.valuesData = [...data.results];
        });
      } else {
        // property scalar type is object_ref, use object ref method
        this.uploadService.searchPropertyValueObjectRefs(event.term, this.property.type.id, this.property.microType)
          .subscribe((data: any) => {
            this.valuesData = [...data.results];
        });
      }
    }
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
          this.unitsData = [...data.results];
        }
    });
  }

  openContextModal() {
    const config = {
      initialState: {
        context: this.property.context,
        title: this.property.type.text
      },
      class: 'modal-lg',
      ignoreBackdropClick: true
    };
    this.modalRef = this.modalService.show(ContextBuilderComponent, config);
    this.modalHiddenSub = this.modalService.onHidden
    .subscribe(() => {
      // emit new instance of value
      // originally was for select2 bug, can be refactored
      const { type, index, required }  = this.property;
      const newProperty = Object.assign(
        new TypedProperty(index, required, type), this.property
        ) as TypedProperty;
      this.typeReselected.emit(newProperty);
      this.modalHiddenSub.unsubscribe();
    });
  }

  setPropertyType(event: Term) {
    // const item = event.data[0];
    this.property.typeTerm = event;

    // clear reset entire property object to clear other select 2 dropdowns
    if (this.property.value || this.property.units) {
      const resetProperty = new TypedProperty(
        this.property.index,
        this.property.required,
        event
      );
      // emit new typed property to replace old one in parent component array reference
      this.typeReselected.emit(resetProperty);
    } else {
      this.getPropertyUnits();
      this.validate();
    }
  }

  setValue(event: Term) {
    this.property.value = event;
    this.validate();
  }

  setUnits(event: Term) {
    this.property.units = event;
    this.validate();
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
