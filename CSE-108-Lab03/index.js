document.addEventListener ("alpine:init", () => {
    Alpine.data("main", () => ({
        visible: "0",
        hidden: null,
        operation: null,
        ephemeral: false,
        operated: false,

        digit (number) {
            this.operated = false;
            if(this.visible === "0" || this.ephemeral) {
                if(number === "0") {
                    return
                }
                this.visible = number;
                this.ephemeral = false
                return;
            }
            this.visible += number;
            console.log(`visible: ${this.visible}`)
            console.log (`hidden: ${this.hidden}`)
        },

        operate () {
            // result = this.visible
            console.log (this.operation)
            this.hidden = parseInt (this.hidden);
            this.visible = parseInt (this.visible);
            if (this.operation === "divide") {
                result = this.hidden / this.visible;
            }
            if (this.operation === "multiply" ) {
                result = this.hidden * this.visible;
            }
            if (this.operation === "add") {
                result = this.hidden + this.visible;
            }
            if (this.operation === "subtract") {
                result = this.hidden - this.visible;
            }
            this.visible = result;
            this.hidden = result;
            this.ephemeral = true
            this.operator = null;
        },

        divide () {
            // console.log(this)
            if(this.hidden === null) {
                this.hidden = this.visible;
                this.ephemeral = true;
                this.operation = "divide"
                return;
            }
            this.operation = "divide"
            if(!this.operated){
                this.operate ();
            }
        },
        multiply () {
            if (this.hidden === null) {
                this.hidden = this.visible;
                this.ephemeral = true;
                this.operation = "multiply"
                return;
            }
            this.operation = "multiply"
            if(!this.operated){
                this.operate ();
            }
        },
        add () {
            if (this.hidden === null) {
                this.hidden = this.visible;
                this.ephemeral = true;
                this.operation = "add"
                return;
            }
            this.operation = "add"
            if(!this.operated){
                this.operate ();
            }
        },
        subtract () {
            if (this.hidden === null) {
                this.hidden = this.visible;
                this.ephemeral = true;
                this.operation = "subtract"
                return;
            }
            this.operation = "subtract"
            if(!this.operated){
                this.operate ();
            }
        },
        equals () {
            if (this.operated) {
                this.clear ();
                return;
            }
            this.operate ();
            this.hidden = this.visible;
            this.operated = true
        },

        clear () {
            this.visible = "0";
            this.hidden = null;
            this.operation = null;
            this.ephemeral = false;
            this.operated = false;
        },

        decimal () {
            if (this.visible.includes (".")) {
                return;
            }
            this.visible += ".";
        }
    }))
})